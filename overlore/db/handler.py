from __future__ import annotations

import json
import os
from sqlite3 import Connection
from threading import Lock
from typing import Any

import sqlean

from overlore.eternum.constants import Realms
from overlore.graphql.constants import EventType as EventKeyHash
from overlore.sqlite.constants import EventType as SqLiteEventType


class DatabaseHandler:
    path: str
    db: Connection
    _instance = None
    realms: Realms

    # create a lock
    lock = Lock()

    def __lock(self) -> None:
        self.lock.acquire(blocking=True, timeout=1000)

    def __release(self) -> None:
        self.lock.release()

    @classmethod
    def instance(cls) -> DatabaseHandler:
        if cls._instance is None:
            print("Creating db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def __init_db(self) -> None:
        self.db.execute("SELECT InitSpatialMetaData(1);")

    def __load_sqlean(self, path: str) -> Connection:
        conn: Connection = sqlean.connect(path)
        # TODO Do we have to load the extension everytime we start up or only once when the db is first created?
        conn.enable_load_extension(True)
        conn.execute('SELECT load_extension("mod_spatialite")')
        return conn

    def __use_initial_queries(self) -> None:
        # Event db definition
        # -> Event type
        # -> pos_1 (maker/attacker)
        # -> pos_2 (taker/target)
        # -> timestamp
        # -> importance
        # -> metadata ()
        self.db.execute(
            """
                            CREATE TABLE IF NOT EXISTS events (
                                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                type INTEGER NOT NULL,
                                importance INTEGER NOT NULL,
                                ts INTEGER NOT NULL,
                                metadata TEXT
                            );
                        """
        )
        # maker/attacker
        self.db.execute("""SELECT AddGeometryColumn('events', 'active_pos', 0, 'POINT', 'XY', 1);""")
        # taker/target
        self.db.execute("""SELECT AddGeometryColumn('events', 'passive_pos', 0, 'POINT', 'XY', 1);""")

    def __insert(self, query: str, values: tuple[Any]) -> int:
        self.__lock()
        cursor = self.db.cursor()
        cursor.execute(query, values)
        self.db.commit()
        added_id = cursor.lastrowid if cursor.lastrowid else 0
        self.__release()
        return added_id

    def __add(self, obj: dict[Any, Any]) -> int:
        event_type = obj["type"]
        del obj["type"]
        active_pos = obj["active_pos"]
        del obj["active_pos"]
        passive_pos = obj["passive_pos"]
        del obj["passive_pos"]
        ts = obj["ts"]
        del obj["ts"]
        obj["importance"]
        del obj["importance"]
        additional_data = json.dumps(obj)
        query = (
            "INSERT INTO events (type, importance, ts, metadata, active_pos, passive_pos) VALUES (?, ?,"
            " ?, ?, MakePoint(?,?),MakePoint(?, ?));"
        )
        values: tuple[Any, ...] = (
            event_type,
            4,
            ts,
            additional_data,
            active_pos[0],
            active_pos[1],
            passive_pos[0],
            passive_pos[1],
        )
        added_id = self.__insert(query, values)
        return added_id

    def __get_event_type(self, obj: Any) -> str:
        return str(obj.get("eventEmitted").get("keys")[0])

    def __parse_resources(self, data: list[Any]) -> tuple[list[Any], list[dict[str, int]]]:
        resource_len = int(data[0], base=16)
        end_idx_resources = resource_len * 2
        resources = [
            {"type": int(data[i], base=16), "amount": int(int(data[i + 1], base=16) / 1000)}
            for i in range(1, end_idx_resources, 2)
        ]
        return (data[end_idx_resources + 1 :], resources)

    def __parse_attacking_entity_ids(self, data: list[Any]) -> tuple[list[Any], list[int]]:
        length = int(data[0], base=16)
        attacking_entity_ids = [int(data[i], base=16) for i in range(1, length)]
        return (data[1 + length :], attacking_entity_ids)

    def __parse_combat_outcome_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event_emitted = event.get("eventEmitted")
        if event_emitted is None:
            raise RuntimeError("eventEmitted no present in event")
        keys = event_emitted.get("keys")
        data = event_emitted.get("data")

        attacker_realm_id = int(keys[1], base=16)
        target_realm_entity_id = int(keys[2], base=16)

        (data, attacking_entity_ids) = self.__parse_attacking_entity_ids(data)
        (data, stolen_resources) = self.__parse_resources(data)

        winner = int(data[0], base=16)
        damage = int(data[1], base=16)
        ts = int(data[2], base=16)

        parsed_event = {
            "type": SqLiteEventType.COMBAT_OUTCOME.value,
            "active_pos": self.realms.position_by_id(attacker_realm_id),
            "passive_pos": self.realms.position_by_id(target_realm_entity_id),
            "attacking_entity_ids": attacking_entity_ids,
            "stolen_resources": stolen_resources,
            "winner": winner,
            "damage": damage,
            "importance": 0,
            "ts": ts,
        }
        return parsed_event

    def __parse_trade_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event_emitted = event.get("eventEmitted")
        if event_emitted is None:
            raise RuntimeError("eventEmitted no present in event")
        keys = event_emitted.get("keys")
        data = event_emitted.get("data")

        _trade_id = int(keys[1], base=16)
        maker_id = int(data[0], base=16)
        taker_id = int(data[1], base=16)

        data = data[2:]

        (data, resources_maker) = self.__parse_resources(data)
        (data, resources_taker) = self.__parse_resources(data)
        ts = int(data[0], base=16)

        parsed_event = {
            "type": SqLiteEventType.ORDER_ACCEPTED.value,
            "active_pos": self.realms.position_by_id(maker_id),
            "passive_pos": self.realms.position_by_id(taker_id),
            "resources_maker": resources_maker,
            "resources_taker": resources_taker,
            "importance": 0,
            "ts": ts,
        }
        return parsed_event

    def init(self, path: str = "./events.db") -> DatabaseHandler:
        db_first_launch = not os.path.exists(path)
        self.db = self.__load_sqlean(path)
        if db_first_launch:
            self.__init_db()
            self.__use_initial_queries()

        self.realms = Realms.instance().init()
        return self

    def get_by_id(self, event_id: int) -> Any:
        self.__lock()
        cursor = self.db.cursor()
        cursor.execute("SELECT id, type, importance, ts, metadata FROM events WHERE id=?", (event_id,))
        ret = cursor.fetchall()
        events_pos = self.get_events_pos_by_id(event_id)
        ret = list(ret) + events_pos
        self.__release()
        return ret

    def get_events_pos_by_id(self, event_id: int) -> Any:
        query = """SELECT X(active_pos), Y(active_pos), X(passive_pos), Y(passive_pos) from events WHERE id=?"""
        cursor = self.db.cursor()
        cursor.execute(query, (event_id,))
        records = cursor.fetchall()
        return [(records[0][0], records[0][1]), (records[0][2], records[0][3])]

    def get_all(self) -> Any:
        query = """SELECT * from events"""
        cursor = self.db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        print("Total rows are:  ", len(records))
        print("Printing each row")
        for row in records:
            for elem in row:
                print(elem)
            print("\n")
        return records

    def process_event(self, event: dict[str, Any]) -> int:
        if self.__get_event_type(event) == EventKeyHash.COMBAT_OUTCOME.value:
            parsed_event = self.__parse_combat_outcome_event(event)
        else:
            parsed_event = self.__parse_trade_event(event)
        return self.__add(parsed_event)
