from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from overlore.db.base_db_handler import BaseDatabaseHandler
from overlore.db.utils import calculate_cosine_similarity, save_to_file
from overlore.prompts.prompts import GptInterface


class VectorDatabaseHandler(BaseDatabaseHandler):
    gpt_conn: None | GptInterface = None
    init_queries: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS townhall (
                discussion text,
                realmID int,
                events_ids text,
                ts text
            );
        """,
        """
            CREATE VIRTUAL TABLE vss_townhall using vss0(
                embedding(1536)
            );
        """,
    ]

    #### Methods used purely for testing
    def vss_version(self) -> str:
        cursor = self.db.cursor()
        (version,) = cursor.execute("select vss_version()").fetchone()
        return str(version)

    def mock_insert(self, data: dict[str, Any]) -> None:
        ts = data["ts"]
        rowid = self._insert(
            "INSERT INTO townhall (discussion, realmID, events_ids, ts) VALUES (?, ?, ?, ?);",
            (data["discussion"], data["realmID"], json.dumps(data["events_ids"]), ts),
        )
        embedding = data["embedding"]
        self._insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))

    def get_all(self) -> tuple[int, int]:
        query = "SELECT * from townhall"
        cursor = self.db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()

        query_vss = """SELECT * from vss_townhall"""
        cursor = self.db.cursor()
        cursor.execute(query_vss)
        records_vss = cursor.fetchall()

        return len(records), len(records_vss)

    ####

    def init(self, path: str = "./vector.db", gpt: None | GptInterface = None) -> VectorDatabaseHandler:
        db_first_launch = not os.path.exists(path)
        self.db = self._load_sqlean(path, ["vector0", "vss0"])
        if db_first_launch:
            self._use_initial_queries(self.init_queries)
        self.gpt_conn = gpt
        return self

    async def insert(self, discussion: str, realmId: int, event_ids: str, save: bool = False) -> None:
        discussion = discussion.strip()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rowid = self._insert(
            "INSERT INTO townhall (discussion, realmID, events_ids, ts) VALUES (?, ?, json_array(?), ?);",
            (discussion, realmId, event_ids, ts),
        )
        if self.gpt_conn:
            embedding = await self.gpt_conn.generateEmbedding(discussion)
            embedding = embedding["data"][0].get("embedding")
            self._insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))

        if save:
            save_to_file(discussion, rowid, embedding)

    def query_nn(self, query_embedding: str, realm_id: int = 2, limit: int = 5) -> list[str]:
        # SQLite version < 3.41
        cursor = self.db.cursor()
        cursor.execute(
            """
            select v.rowid, v.distance from vss_townhall v
            inner join townhall t on v.rowid = t.rowid
            where t.realmID = ? and vss_search(embedding, vss_search_params(?, ?))
            """,
            (realm_id, json.dumps(query_embedding), limit),
        )
        results = cursor.fetchall()
        return results

    def query_cosine_similarity(self, query_embedding: list[float]) -> list:
        cursor = self.db.cursor()
        cursor.execute(
            """
            select rowid, embedding from vss_townhall
            """
        )
        results = cursor.fetchall()

        res = []
        for row in results:
            res.append({row[0]: calculate_cosine_similarity(query_embedding, row[1])})
        return res

    def query_event_ids(self, event_id: int) -> tuple[int | str, bool]:
        cursor = self.db.cursor()
        cursor.execute(
            """
            select townhall.discussion from townhall, json_each(townhall.events_ids) as ev_id
            where ev_id.value = ?
            ORDER BY townhall.ts DESC
            LIMIT 1;
            """,
            (event_id,),
        )
        results = cursor.fetchall()

        if not results:
            return event_id, False

        # results: list[tuple]
        return results[0][0], True
