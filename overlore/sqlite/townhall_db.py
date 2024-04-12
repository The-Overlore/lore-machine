from __future__ import annotations

import json
import logging
from sqlite3 import Connection
from typing import Tuple, cast

import sqlite_vss

from overlore.errors import ErrorCodes
from overlore.sqlite.base_db import A_TIME, BaseDatabase, average, decay_function
from overlore.sqlite.errors import CosineSimilarityNotFoundError

logger = logging.getLogger("overlore")


class TownhallDatabase(BaseDatabase):
    _instance: TownhallDatabase | None = None
    EXTENSIONS: list[str] = []
    MIGRATIONS: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS townhall (
                discussion TEXT,
                townhall_input TEXT,
                input_score INT,
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
                poignancy INTEGER,
                ts INTEGER
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
        self._init(
            path=path,
            extensions=self.EXTENSIONS,
            migrations=self.MIGRATIONS,
            functions=[("average", -1, average), ("decayFunction", 3, decay_function)],
            preload=self._preload,
        )
        return self

    def get_highest_scoring_thought(
        self, query_embedding: list[float], npc_entity_id: int, katana_ts: int
    ) -> tuple[str, int, float, float]:
        query = """
            SELECT thought, ts, cos_similarity, score FROM (
                SELECT thought, average(cos_similarity, poignancy, decayFunction(?, 10, ? - ts)) as score, cos_similarity, ts
                FROM(
                    SELECT vss_cosine_similarity(?, vss_npc_thought.embedding) * 10.0 AS cos_similarity, npc_thought.thought, npc_thought.poignancy, npc_thought.ts
                    FROM vss_npc_thought
                    INNER JOIN npc_thought ON vss_npc_thought.rowid = npc_thought.rowid
                    WHERE npc_thought.npc_entity_id = ?
                )
                ORDER BY score DESC
            )
        """
        values = (
            A_TIME,
            katana_ts,
            json.dumps(query_embedding),
            npc_entity_id,
        )

        res = self.execute_query(query, values)

        if not res:
            raise CosineSimilarityNotFoundError(f"No similar thought found for npc entity {npc_entity_id}")

        return cast(Tuple[str, int, float, float], res[0])

    def insert_townhall_discussion(
        self, realm_id: int, discussion: str, townhall_input: str, input_score: int, ts: int
    ) -> int:
        discussion = discussion.strip()

        return self._insert(
            "INSERT INTO townhall (discussion, townhall_input, input_score, realm_id, ts) VALUES (?, ?, ?, ?, ?);",
            (discussion, townhall_input, input_score, realm_id, ts),
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
        self, npc_entity_id: int, thought: str, poignancy: int, katana_ts: int, thought_embedding: list[float]
    ) -> int:
        if len(thought_embedding) == 0:
            raise RuntimeError(ErrorCodes.INSERTING_EMPTY_EMBEDDING)

        added_row_id = self._insert(
            "INSERT INTO npc_thought (npc_entity_id, thought, poignancy, ts) VALUES (?, ?, ?, ?);",
            (npc_entity_id, thought, poignancy, katana_ts),
        )
        self._insert(
            "INSERT INTO vss_npc_thought (rowid, embedding) VALUES (?, ?);",
            (added_row_id, json.dumps(thought_embedding)),
        )
        return added_row_id

    def fetch_npc_thought_by_row_id(self, row_id: int) -> str:
        self.execute_query("SELECT thought FROM npc_thought WHERE rowid = ?;", (row_id,))
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
