from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from overlore.prompts.prompts import GptInterface
from overlore.sqlite.db import Database
from overlore.sqlite.types import StoredVector, TownhallEventResponse


def save_to_file(discussion: str, rowid: int, embedding: str) -> None:
    with open("Output.json", "a") as file:
        data_to_save = {"rowid": rowid, "discussion": discussion, "embedding": embedding}
        json.dump(data_to_save, file)
        file.write("\n")


class VectorDatabase(Database):
    _instance: VectorDatabase | None = None
    GPT_CONN: GptInterface | None = None
    EXTENSIONS: list[str] = ["vector0", "vss0"]
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

    def init(self, path: str = "./vector.db", gpt_interface: GptInterface | None = None) -> VectorDatabase:
        # Call parent init function
        self._init(
            path,
            self.EXTENSIONS,
            self.FIRST_BOOT_QUERIES,
            [],
        )
        self.GPT_CONN = gpt_interface
        return self

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
            save_to_file(discussion, rowid, embedding)

    def query_nearest_neighbour(self, query_embedding: str, realm_id: int, limit: int = 1) -> list[StoredVector]:
        # SQLite version < 3.41
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

    def query_event_ids(self, event_id: int) -> TownhallEventResponse:
        query = """
            select townhall.discussion from townhall, json_each(townhall.events_ids) as ev_id
            where ev_id.value = ?
            ORDER BY townhall.ts DESC
            LIMIT 1;
        """
        values = (event_id,)
        res = self.execute_query(query, values)

        if not res:
            return event_id, False
        return res[0][0], True
