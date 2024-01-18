from __future__ import annotations

import json
from datetime import datetime
from sqlite3 import Connection
from typing import Any

import sqlite_vss

from overlore.prompts.prompts import GptInterface
from overlore.sqlite.db import Database
from overlore.sqlite.types import StoredVector


class VectorDatabase(Database):
    _instance: VectorDatabase | None = None
    GPT_CONN: GptInterface | None = None
    EXTENSIONS: list[str] = []
    FIRST_BOOT_QUERIES: list[str] = [
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

    @classmethod
    def instance(cls) -> VectorDatabase:
        if cls._instance is None:
            print("Creating vector db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def _preload(self, db: Connection) -> None:
        sqlite_vss.load(db)

    def init(self, path: str = "./vector.db", gpt_interface: GptInterface | None = None) -> VectorDatabase:
        # Call parent init function
        self._init(path, self.EXTENSIONS, self.FIRST_BOOT_QUERIES, [], self._preload)
        self.GPT_CONN = gpt_interface
        return self

    def save_to_file(self, discussion: str, rowid: int, embedding: str) -> None:
        with open("Output.json", "a") as file:
            data_to_save = {"rowid": rowid, "discussion": discussion, "embedding": embedding}
            json.dump(data_to_save, file)
            file.write("\n")

    def mock_insert(self, data: dict[str, Any]) -> None:
        ts = data["ts"]
        rowid = self._insert(
            "INSERT INTO townhall (discussion, realmID, events_ids, ts) VALUES (?, ?, ?, ?);",
            (data["discussion"], data["realmID"], json.dumps(data["events_ids"]), ts),
        )

        embedding = data["embedding"]
        self._insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))

    def get_all(self) -> tuple[int, int]:
        query = "SELECT * FROM townhall"
        records = self.execute_query(query, ())

        vss_query = "SELECT * FROM vss_townhall"
        records_vss = self.execute_query(vss_query, ())

        return len(records), len(records_vss)

    async def insert_townhall_discussion(
        self, discussion: str, realmId: int, event_ids: str, save: bool = False
    ) -> None:
        discussion = discussion.strip()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rowid = self._insert(
            "INSERT INTO townhall (discussion, realmID, events_ids, ts) VALUES (?, ?, json_array(?), ?);",
            (discussion, realmId, event_ids, ts),
        )
        if self.GPT_CONN:
            embedding = await self.GPT_CONN.generateEmbedding(discussion)
            embedding = embedding["data"][0].get("embedding")
            self._insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))

        if save:
            self.save_to_file(discussion, rowid, embedding)

    def query_nearest_neighbour(self, query_embedding: str, realm_id: int, limit: int = 1) -> list[StoredVector]:
        # Use vss_search for SQLite version < 3.41 else vss_search_params db function
        query = """
            select v.rowid, v.distance from vss_townhall v
            inner join townhall t on v.rowid = t.rowid
            where t.realmID = ? and vss_search(embedding, vss_search_params(?, ?))
        """
        values = (realm_id, json.dumps(query_embedding), limit + 1)
        return self.execute_query(query, values)

    def query_cosine_similarity(self, query_embedding: list[float]) -> list[StoredVector]:
        query = """
            SELECT rowid, vss_cosine_similarity(?, embedding) as similarity
            FROM vss_townhall
            ORDER BY similarity DESC
            LIMIT 1;
        """
        values = (json.dumps(query_embedding),)
        return self.execute_query(query, values)

    def query_event_ids(self, event_id: list[int]) -> tuple[int, str | None]:
        query = """
            WITH GivenEventIDs(event_id) AS (VALUES (?), (?), (?), (?), (?)),
            RecentDiscussions AS (
                SELECT
                    json_each.value AS event_id,
                    T.discussion,
                    T.ts,
                    T.rowid,
                    ROW_NUMBER() OVER (PARTITION BY json_each.value ORDER BY T.ts DESC) as rn
                FROM
                    townhall T, json_each(T.events_ids)
                WHERE
                    json_each.value IN ((?), (?), (?), (?), (?))
            ),
            DupDiscussions AS (
                SELECT
                    event_id,
                    discussion,
                    rowid,
                    ROW_NUMBER() OVER (PARTITION BY rowid ORDER BY ts DESC) as dup_rn
                FROM
                    RecentDiscussions
                WHERE
                    rn = 1
            )
            SELECT
                event_id,
                discussion
            FROM
                DupDiscussions
            WHERE
                dup_rn = 1
            UNION ALL
            SELECT
                event_id,
                NULL AS discussion
            FROM
                GivenEventIDs
            WHERE
                event_id NOT IN (SELECT event_id FROM RecentDiscussions WHERE rn = 1)
        """
        values = (
            event_id[0],
            event_id[1],
            event_id[2],
            event_id[3],
            event_id[4],
            event_id[0],
            event_id[1],
            event_id[2],
            event_id[3],
            event_id[4],
        )
        res = self.execute_query(query, values)

        return res
