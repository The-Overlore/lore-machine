from __future__ import annotations

import json
import logging
from sqlite3 import Connection
from typing import cast

import sqlite_vss

from overlore.sqlite.base_db import BaseDatabase
from overlore.sqlite.errors import CosineSimilarityNotFoundError
from overlore.sqlite.types import StoredVector

logger = logging.getLogger("overlore")


class TownhallDatabase(BaseDatabase):
    _instance: TownhallDatabase | None = None
    EXTENSIONS: list[str] = []
    FIRST_BOOT_QUERIES: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS townhall (
                discussion TEXT,
                townhall_input TEXT,
                realm_id INTEGER NOT NULL,
                ts INTEGER NOT NULL
            );
        """,
        """
            CREATE TABLE IF NOT EXISTS daily_townhall_tracker (
                realm_id INTEGER NOT NULL,
                event_row_id TEXT
            );
        """,
        """
            CREATE TABLE IF NOT EXISTS npc_thought (
                npc_entity_id INTEGER NOT NULL,
                thought TEXT,
                poignancy INTEGER
            );
        """,
        """
            CREATE VIRTUAL TABLE IF NOT EXISTS vss_npc_thought using vss0(
                embedding(1536)
            );
        """,
    ]

    @classmethod
    def instance(cls) -> TownhallDatabase:
        if cls._instance is None:
            logger.debug("Creating townhall db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def _preload(self, db: Connection) -> None:
        sqlite_vss.load(db)

    def init(self, path: str = "./databases/townhall.db") -> TownhallDatabase:
        self._init(path, self.EXTENSIONS, self.FIRST_BOOT_QUERIES, [], self._preload)
        return self

    def query_cosine_similarity(
        self, query_embedding: list[float], npc_entity_id: int, limit: int = 1
    ) -> list[StoredVector]:
        if limit <= 0:
            raise ValueError("Limit must be higher than 0")

        query = """
            SELECT vectorized_thought.rowid, vss_cosine_similarity(?, embedding) AS cos_similarity
            FROM vss_npc_thought vectorized_thought
            INNER JOIN npc_thought thought ON vectorized_thought.rowid = thought.rowid
            WHERE thought.npc_entity_id = ?
            ORDER BY cos_similarity DESC
            LIMIT ?;
        """

        values = (json.dumps(query_embedding), npc_entity_id, limit)
        res = self.execute_query(query, values)
        if not res:
            raise CosineSimilarityNotFoundError(f"No similar thought found for npc entity {npc_entity_id}")
        return cast(list[StoredVector], res)

    def insert_townhall_discussion(self, realm_id: int, discussion: str, townhall_input: str, ts: int) -> int:
        discussion = discussion.strip()

        return self._insert(
            "INSERT INTO townhall (discussion, townhall_input, realm_id, ts) VALUES (?, ?, ?, ?);",
            (discussion, townhall_input, realm_id, ts),
        )

    def fetch_townhalls_by_realm_id(self, realm_id: int) -> list:
        return self.execute_query(
            "SELECT discussion, townhall_input FROM townhall WHERE realm_id = ? ORDER BY ts DESC;",
            (realm_id,),
        )

    def fetch_last_townhall_ts_by_realm_id(self, realm_id: int) -> int:
        last_ts = self.execute_query(
            "SELECT ts FROM townhall WHERE realm_id = ? ORDER BY ts DESC LIMIT 1;",
            (realm_id,),
        )

        if last_ts:
            return cast(int, last_ts[0][0])
        return -1

    def insert_npc_thought(
        self, npc_entity_id: int, thought: str, poignancy: int, thought_embedding: list[float]
    ) -> int:
        added_row_id = self._insert(
            "INSERT INTO npc_thought (npc_entity_id, thought, poignancy) VALUES (?, ?, ?);",
            (npc_entity_id, thought, poignancy),
        )
        self._insert(
            "INSERT INTO vss_npc_thought (rowid, embedding) VALUES (?, ?);",
            (added_row_id, json.dumps(thought_embedding)),
        )
        return added_row_id

    def fetch_npc_thought_by_row_id(self, row_id: int) -> str:
        return cast(str, self.execute_query("SELECT thought FROM npc_thought WHERE rowid = ?;", (row_id,))[0][0])

    def fetch_daily_townhall_tracker(self, realm_id: int) -> list[int]:
        result = self.execute_query("SELECT event_row_id FROM daily_townhall_tracker WHERE realm_id = ?;", (realm_id,))
        if result:
            stored_event_row_ids = json.loads(result[0][0])
            return cast(list[int], stored_event_row_ids)
        return []

    def insert_or_update_daily_townhall_tracker(self, realm_id: int, event_row_id: int) -> int:
        stored_event_row_ids = self.fetch_daily_townhall_tracker(realm_id)

        if len(stored_event_row_ids) == 0:
            query = """
                INSERT INTO daily_townhall_tracker(realm_id, event_row_id)
                VALUES (?, json_array(?));
            """
            insert_values = (realm_id, event_row_id)
            return self._insert(query, insert_values)
        else:
            stored_event_row_ids.append(event_row_id)
            event_row_ids_count = ",".join(["?" for _ in stored_event_row_ids])

            query = f"""
                UPDATE daily_townhall_tracker
                SET event_row_id = json_array({event_row_ids_count})
                WHERE realm_id = ?;
            """
            update_values = (*stored_event_row_ids, realm_id)
            return self._update(query, update_values)

    def delete_daily_townhall_tracker(self, realm_id: int) -> None:
        query = """
            DELETE FROM daily_townhall_tracker WHERE realm_id = ?;
        """
        values = (realm_id,)

        self._delete(query, values)
