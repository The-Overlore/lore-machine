from __future__ import annotations

import json
from typing import Any, cast

from overlore.db.base_db_handler import Database
from overlore.eternum.constants import Realms
from overlore.eternum.types import RealmPosition
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
                importance INTEGER NOT NULL,
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

    def insert_event(self, obj: ParsedEvent) -> int:
        event_type = obj["type"]
        del obj["type"]
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
            "INSERT INTO events (type, importance, ts, metadata, active_pos, passive_pos) VALUES (?, ?,"
            " ?, ?, MakePoint(?,?),MakePoint(?, ?));"
        )
        values: tuple[Any, ...] = (
            event_type,
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

    def init(self, path: str = "./events.db") -> EventsDatabase:
        # Call parent init function
        self._init(
            path,
            self.EXTENSIONS,
            self.FIRST_BOOT_QUERIES,
            [("decayFunction", 3, decayFunction), ("average", 3, average), ("minus", 2, average)],
        )
        self.realms = Realms.instance().init()
        return self

    def get_by_id(self, event_id: int) -> StoredEvent:
        records = self.execute_query(
            "SELECT rowid, type, importance, ts, metadata, X(active_pos), Y(active_pos), X(passive_pos), Y(passive_pos)"
            " FROM events WHERE rowid=?",
            (event_id,),
        )
        record = list(records[0])
        return [*record[:5], (record[5], record[6]), (record[7], record[8])]

    def get_all(self) -> list[StoredEvent]:
        query = """SELECT rowid, type, importance, ts, metadata, X(active_pos), Y(active_pos), X(passive_pos), Y(passive_pos) from events ORDER BY rowid ASC"""
        records = self.execute_query(query, ())
        AllEvents: list[StoredEvent] = [[*tup[:5], (tup[5], tup[6]), (tup[7], tup[8])] for tup in records]
        return AllEvents

    def fetch_most_relevant(self, realm_position: list[int], current_time: int) -> Any:
        query = """SELECT
                        rowid,
                        average(
                            decayFunction(?, 10,
                                MIN(
                                    Distance(MakePoint(?,?), active_pos),
                                    Distance(MakePoint(?,?), passive_pos)
                                )
                            ),
                            decayFunction(?, 10, ? - ts),
                            importance
                        )
                    as RET from events ORDER BY RET DESC LIMIT 5"""
        params = (
            A_DISTANCE,
            realm_position[0],
            realm_position[1],
            realm_position[0],
            realm_position[1],
            A_TIME,
            current_time,
        )
        return self.execute_query(query=query, params=params)
