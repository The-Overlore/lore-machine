from __future__ import annotations

import json
import logging
from copy import deepcopy
from sqlite3 import Connection
from typing import Any, cast

from overlore.eternum.constants import Realms
from overlore.eternum.types import RealmPosition
from overlore.sqlite.db import Database
from overlore.sqlite.types import StoredEvent
from overlore.types import ParsedEvent

logger = logging.getLogger("overlore")

MAX_TIME_DAYS = 7
MAX_TIME_S = MAX_TIME_DAYS * 24.0 * 60.0 * 60.0
MAX_DISTANCE_M = 10000

A_TIME = float(-10.0 / MAX_TIME_S)
A_DISTANCE = float(-10.0 / MAX_DISTANCE_M)

QUERY_RES_POS_INDEX_START = 9


def decayFunction(a: float, b: float, x: float) -> float:
    y = (a * x) + b
    if y < 0.0:
        return 0.0
    if y > 10.0:
        return 10.0
    else:
        return y


def minus(a: float, b: float) -> float:
    return a - b


def average(a: float, b: float, c: float) -> float:
    return (a + b + c) / 3


class EventsDatabase(Database):
    _instance: EventsDatabase | None = None
    realms: Realms

    EXTENSIONS = ["mod_spatialite"]
    FIRST_BOOT_QUERIES = [
        # this needs to be executed first
        """SELECT InitSpatialMetaData(1);""",
        """
            CREATE TABLE IF NOT EXISTS events (
                type INTEGER NOT NULL,
                torii_event_id TEXT,
                active_realm_entity_id INTEGER NOT NULL,
                active_realm_id INTEGER NOT NULL,
                passive_realm_entity_id INTEGER NOT NULL,
                passive_realm_id INTEGER NOT NULL,
                importance FLOAT NOT NULL,
                ts INTEGER NOT NULL,
                metadata TEXT
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
        # noop
        pass

    def init(self, path: str = "./events.db") -> EventsDatabase:
        # Call parent init function
        self._init(
            path,
            self.EXTENSIONS,
            self.FIRST_BOOT_QUERIES,
            [("decayFunction", 3, decayFunction), ("average", 3, average), ("minus", 2, average)],
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
        event_copy = deepcopy(event)

        torii_event_id = event["torii_event_id"]
        del event["torii_event_id"]
        event_type = event["type"]
        del event["type"]
        active_realm_entity_id = event["active_realm_entity_id"]
        del event["active_realm_entity_id"]
        active_realm_id = event["active_realm_id"]
        del event["active_realm_id"]
        passive_realm_entity_id = event["passive_realm_entity_id"]
        del event["passive_realm_entity_id"]
        passive_realm_id = event["passive_realm_id"]
        del event["passive_realm_id"]
        active_pos = cast(RealmPosition, event["active_pos"])
        del event["active_pos"]
        passive_pos = cast(RealmPosition, event["passive_pos"])
        del event["passive_pos"]
        ts = event["ts"]
        del event["ts"]
        importance = event["importance"]
        del event["importance"]
        additional_data = json.dumps(event)
        query = (
            "INSERT INTO events (torii_event_id, type, active_realm_entity_id, active_realm_id,"
            " passive_realm_entity_id, passive_realm_id, importance, ts, metadata, active_pos, passive_pos) SELECT ?,"
            " ?, ?, ?, ?, ?, ?, ?, ?, MakePoint(?,?),MakePoint(?, ?) WHERE NOT EXISTS (SELECT 1 FROM events WHERE"
            " torii_event_id=?);"
        )
        values: tuple[Any, ...] = (
            torii_event_id,
            event_type,
            active_realm_entity_id,
            active_realm_id,
            passive_realm_entity_id,
            passive_realm_id,
            importance,
            ts,
            additional_data,
            active_pos[0],
            active_pos[1],
            passive_pos[0],
            passive_pos[1],
            torii_event_id,
        )

        added_id: int = self._insert(query, values)

        logger.info(f"Stored event received at rowid {added_id}: {event_copy}")

        return added_id

    def get_by_ids(self, event_ids: list[int]) -> list[StoredEvent]:
        placeholders = ", ".join(["?" for _ in event_ids])
        records = self.execute_query(
            "SELECT rowid, type, active_realm_entity_id, active_realm_id, passive_realm_entity_id, passive_realm_id,"
            " importance, ts, metadata, X(active_pos), Y(active_pos), X(passive_pos), Y(passive_pos) FROM events WHERE"
            f" rowid IN ({placeholders})",
            (*event_ids,),
        )

        return self.format_records(records=records)

    def get_all(self) -> list[StoredEvent]:
        query = """SELECT rowid, type, active_realm_entity_id, active_realm_id, passive_realm_entity_id, passive_realm_id, importance, ts, metadata, X(active_pos), Y(active_pos), X(passive_pos), Y(passive_pos) from events ORDER BY rowid ASC"""
        records = self.execute_query(query, ())

        return self.format_records(records=records)

    def fetch_most_relevant(self, realm_position: RealmPosition, current_time: int) -> list[StoredEvent]:
        """Attributes an importance score depending on the distance in kilometers, the recency
        and general importance score of an event, then gets the 5 events that scored the highest"""
        query = """SELECT
                    rowid,
                    type,
                    active_realm_entity_id,
                    active_realm_id,
                    passive_realm_entity_id,
                    passive_realm_id,
                    importance,
                    ts,
                    metadata,
                    X(active_pos),
                    Y(active_pos),
                    X(passive_pos),
                    Y(passive_pos)
                    FROM (
                        SELECT
                            rowid,
                            type,
                            active_realm_entity_id,
                            active_realm_id,
                            passive_realm_entity_id,
                            passive_realm_id,
                            importance,
                            ts,
                            metadata,
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
        return self.format_records(records=records)
