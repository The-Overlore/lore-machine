from __future__ import annotations

import json
from sqlite3 import Connection
from typing import Any, cast

from overlore.eternum.constants import Realms
from overlore.eternum.types import RealmPosition
from overlore.sqlite.db import Database
from overlore.sqlite.types import StoredEvent
from overlore.types import ParsedEvent

MAX_TIME_DAYS = 7
MAX_TIME_S = MAX_TIME_DAYS * 24.0 * 60.0 * 60.0
MAX_DISTANCE_M = 10000

A_TIME = float(-10.0 / MAX_TIME_S)
A_DISTANCE = float(-10.0 / MAX_DISTANCE_M)


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
                active_realm_entity_id INTEGER NOT NULL,
                passive_realm_entity_id INTEGER NOT NULL,
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
            print("Creating events db interface")
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

    def insert_event(self, obj: ParsedEvent) -> int:
        event_type = obj["type"]
        del obj["type"]
        active_realm_entity_id = obj["active_realm_entity_id"]
        del obj["active_realm_entity_id"]
        passive_realm_entity_id = obj["passive_realm_entity_id"]
        del obj["passive_realm_entity_id"]
        active_pos = cast(RealmPosition, obj["active_pos"])
        del obj["active_pos"]
        passive_pos = cast(RealmPosition, obj["passive_pos"])
        del obj["passive_pos"]
        ts = obj["ts"]
        del obj["ts"]
        importance = obj["importance"]
        del obj["importance"]
        additional_data = json.dumps(obj)
        query = (
            "INSERT INTO events (type, active_realm_entity_id, passive_realm_entity_id, importance, ts, metadata,"
            " active_pos, passive_pos) VALUES (?, ?, ?, ?, ?, ?, MakePoint(?,?),MakePoint(?, ?));"
        )
        values: tuple[Any, ...] = (
            event_type,
            active_realm_entity_id,
            passive_realm_entity_id,
            importance,
            ts,
            additional_data,
            active_pos[0],
            active_pos[1],
            passive_pos[0],
            passive_pos[1],
        )
        added_id: int = self._insert(query, values)
        return added_id

    def get_by_ids(self, event_ids: list[int]) -> list[StoredEvent]:
        placeholders = ", ".join(["?" for _ in event_ids])
        records = self.execute_query(
            "SELECT rowid, type, active_realm_entity_id, passive_realm_entity_id, importance, ts, metadata,"
            " X(active_pos), Y(active_pos), X(passive_pos), Y(passive_pos) FROM events WHERE rowid IN"
            f" ({placeholders})",
            (*event_ids,),
        )
        events: list[StoredEvent] = [[*tup[:7], (tup[7], tup[8]), (tup[9], tup[10])] for tup in records]
        return events

    def get_all(self) -> list[StoredEvent]:
        query = """SELECT rowid, type, active_realm_entity_id, passive_realm_entity_id, importance, ts, metadata, X(active_pos), Y(active_pos), X(passive_pos), Y(passive_pos) from events ORDER BY rowid ASC"""
        records = self.execute_query(query, ())
        AllEvents: list[StoredEvent] = [[*tup[:7], (tup[7], tup[8]), (tup[9], tup[10])] for tup in records]
        return AllEvents

    def fetch_most_relevant(self, realm_position: RealmPosition, current_time: int) -> list[StoredEvent]:
        """Attributes an importance score depending on the distance in kilometers, the recency
        and general importance score of an event, then gets the 5 events that scored the highest"""
        query = """SELECT
                    rowid,
                    type,
                    active_realm_entity_id,
                    passive_realm_entity_id,
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
                            passive_realm_entity_id,
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
                    ORDER BY score DESC LIMIT 5"""
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
        events: list[StoredEvent] = [[*tup[:7], (tup[7], tup[8]), (tup[9], tup[10])] for tup in records]
        return events
