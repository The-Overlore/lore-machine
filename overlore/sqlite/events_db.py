from __future__ import annotations

import logging
from sqlite3 import Connection
from typing import Any, cast

from overlore.eternum.realms import Realms
from overlore.eternum.types import RealmPosition
from overlore.sqlite.base_db import A_DISTANCE, A_TIME, BaseDatabase, average, decay_function
from overlore.sqlite.types import StoredEvent
from overlore.types import ParsedEvent

logger = logging.getLogger("overlore")

QUERY_RES_POS_INDEX_START = 9


class EventsDatabase(BaseDatabase):
    _instance: EventsDatabase | None = None
    realms: Realms

    EXTENSIONS = ["mod_spatialite"]
    MIGRATIONS = [
        # this needs to be executed first
        """SELECT InitSpatialMetaData(1);""",
        """
            CREATE TABLE IF NOT EXISTS events (
                event_type INTEGER NOT NULL,
                torii_event_id TEXT,
                active_realm_entity_id INTEGER NOT NULL,
                active_realm_id INTEGER NOT NULL,
                passive_realm_entity_id INTEGER NOT NULL,
                passive_realm_id INTEGER NOT NULL,
                importance FLOAT NOT NULL,
                ts INTEGER NOT NULL,
                type_specific_data TEXT
            );
        """,
        # maker/attacker
        """SELECT AddGeometryColumn('events', 'active_pos', 0, 'POINT', 'XY', 1);""",
        # taker/target
        """SELECT AddGeometryColumn('events', 'passive_pos', 0, 'POINT', 'XY', 1);""",
    ]

    @classmethod
    def instance(cls) -> EventsDatabase:
        if cls._instance is None:
            logger.debug("Creating events db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def _preload(self, db: Connection) -> None:
        pass

    def init(self, path: str = "./databases/events.db") -> EventsDatabase:
        # Call parent init function
        self._init(
            path,
            self.EXTENSIONS,
            self.MIGRATIONS,
            [("decayFunction", 3, decay_function), ("average", -1, average)],
            self._preload,
        )
        self.realms = Realms.instance().init()
        return self

    def format_records(self, records: list[Any]) -> list[StoredEvent]:
        return cast(
            list[StoredEvent],
            [
                [
                    *tup[:QUERY_RES_POS_INDEX_START],
                    (tup[QUERY_RES_POS_INDEX_START], tup[QUERY_RES_POS_INDEX_START + 1]),
                    (tup[QUERY_RES_POS_INDEX_START + 2], tup[QUERY_RES_POS_INDEX_START + 3]),
                ]
                for tup in records
            ],
        )

    def insert_event(self, event: ParsedEvent) -> int:
        query = (
            "INSERT INTO events (torii_event_id, event_type, active_realm_entity_id, active_realm_id,"
            " passive_realm_entity_id, passive_realm_id, importance, ts, type_specific_data, active_pos, passive_pos)"
            " SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, MakePoint(?,?),MakePoint(?, ?) WHERE NOT EXISTS (SELECT 1 FROM events"
            " WHERE torii_event_id=?);"
        )
        values: tuple[Any, ...] = (
            event["torii_event_id"],
            event["event_type"],
            event["active_realm_entity_id"],
            event["active_realm_id"],
            event["passive_realm_entity_id"],
            event["passive_realm_id"],
            event["importance"],
            event["ts"],
            event["type_specific_data"],
            event["active_pos"][0],
            event["active_pos"][1],
            event["passive_pos"][0],
            event["passive_pos"][1],
            event["torii_event_id"],
        )

        added_id: int = self._insert(query, values)

        if added_id != 0:
            logger.info(f"Stored event received at rowid {added_id}: {event}")

        return added_id

    def get_by_ids(self, event_ids: list[int]) -> list[StoredEvent]:
        placeholders = ", ".join(["?" for _ in event_ids])
        records = self.execute_query(
            "SELECT rowid, event_type, active_realm_entity_id, active_realm_id, passive_realm_entity_id,"
            " passive_realm_id, importance, ts, type_specific_data, X(active_pos), Y(active_pos), X(passive_pos),"
            f" Y(passive_pos) FROM events WHERE rowid IN ({placeholders})",
            (*event_ids,),
        )

        return self.format_records(records=records)

    def get_all(self) -> list[StoredEvent]:
        query = """SELECT rowid, event_type, active_realm_entity_id, active_realm_id, passive_realm_entity_id, passive_realm_id, importance, ts, type_specific_data, X(active_pos), Y(active_pos), X(passive_pos), Y(passive_pos) from events ORDER BY rowid ASC"""
        records = self.execute_query(query, ())

        return self.format_records(records=records)

    def fetch_most_relevant_event(
        self, realm_position: RealmPosition, current_time: int, stored_event_row_ids: list[int]
    ) -> StoredEvent | None:
        where_clauses = " AND ".join([f"rowid != {event_id}" for event_id in stored_event_row_ids])
        where_clauses = "WHERE " + where_clauses if where_clauses != "" else ""

        """Attributes an importance score depending on the distance in kilometers, the recency
        and general importance score of an event, then gets the event that scored the highest"""
        query = f"""SELECT
                    rowid,
                    event_type,
                    active_realm_entity_id,
                    active_realm_id,
                    passive_realm_entity_id,
                    passive_realm_id,
                    importance,
                    ts,
                    type_specific_data,
                    X(active_pos),
                    Y(active_pos),
                    X(passive_pos),
                    Y(passive_pos)
                    FROM (
                        SELECT
                            rowid,
                            event_type,
                            active_realm_entity_id,
                            active_realm_id,
                            passive_realm_entity_id,
                            passive_realm_id,
                            importance,
                            ts,
                            type_specific_data,
                            active_pos,
                            passive_pos,
                            average(
                                decayFunction(?, 10,
                                    MIN(
                                        Distance(MakePoint(?,?), active_pos),
                                        Distance(MakePoint(?,?), passive_pos)
                                    )
                                ),
                                decayFunction(?, 10, ? - ts),
                                importance
                            ) as score
                        FROM events
                        {where_clauses}
                    )
                    ORDER BY score DESC LIMIT 1"""
        params = (
            A_DISTANCE,
            realm_position[0],
            realm_position[1],
            realm_position[0],
            realm_position[1],
            A_TIME,
            current_time,
        )

        records = self.execute_query(query=query, params=params)
        return self.format_records(records=records)[0] if len(records) > 0 else None
