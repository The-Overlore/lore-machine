from __future__ import annotations

import json
import logging
from datetime import datetime
from sqlite3 import Connection

import sqlite_vss

from overlore.sqlite.db import Database
from overlore.sqlite.types import StoredVector

logger = logging.getLogger("overlore")


class VectorDatabase(Database):
    _instance: VectorDatabase | None = None
    EXTENSIONS: list[str] = []
    FIRST_BOOT_QUERIES: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS townhall (
                discussion text,
                summary text,
                realm_id int,
                event_id int,
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
            logger.debug("Creating vector db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def _preload(self, db: Connection) -> None:
        sqlite_vss.load(db)

    def init(self, path: str = "./vector.db") -> VectorDatabase:
        # Call parent init function
        self._init(path, self.EXTENSIONS, self.FIRST_BOOT_QUERIES, [], self._preload)
        return self

    def get_entries_count(self) -> tuple[int, int]:
        query = "SELECT rowid FROM townhall"
        records = self.execute_query(query, ())

        vss_query = "SELECT rowid FROM vss_townhall"
        records_vss = self.execute_query(vss_query, ())

        return len(records), len(records_vss)

    def insert_townhall_discussion(
        self, discussion: str, summary: str, realm_id: int, event_id: int, embedding: list[float]
    ) -> int:
        discussion = discussion.strip()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rowid = self._insert(
            "INSERT INTO townhall (discussion, summary, realm_id, event_id, ts) VALUES (?, ?, ?, ?, ?);",
            (discussion, summary, realm_id, event_id, ts),
        )
        self._insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))
        return rowid

    def query_nearest_neighbour(self, query_embedding: str, realm_id: int, limit: int = 1) -> list[StoredVector]:
        if limit <= 0:
            raise ValueError("Limit must be higher than 0")
        if self.get_entries_count() == (0, 0):
            return []

        # Use vss_search for SQLite version < 3.41 else vss_search_params db function
        query = """
            SELECT v.rowid, v.distance FROM vss_townhall v
            INNER JOIN townhall t ON v.rowid = t.rowid
            WHERE t.realm_id = ? AND vss_search(embedding, vss_search_params(?, ?))
        """

        values = (realm_id, json.dumps(query_embedding), limit + 1)

        return self.execute_query(query, values)

    def query_cosine_similarity(
        self, query_embedding: list[float], realm_id: int, limit: int = 1
    ) -> list[StoredVector]:
        if limit <= 0:
            raise ValueError("Limit must be higher than 0")

        query = """
            SELECT v.rowid, vss_cosine_similarity(?, embedding) AS similarity
            FROM vss_townhall v
            INNER JOIN townhall t ON v.rowid = t.rowid
            WHERE t.realm_id = ?
            ORDER BY similarity DESC
            LIMIT ?;
        """
        values = (json.dumps(query_embedding), realm_id, limit)
        return self.execute_query(query, values)

    def get_townhall_from_event(self, event_id: int, realm_id: int) -> str | None:
        """
        Returns tuple of:
            - List of townhalls summary. One event_id of the list given in parameter must have been involved in the generation of the discussion.
            - Events_ids in the list given in parameter which haven't generated any summary before
        """
        query = """
            SELECT summary FROM townhall WHERE event_id = ? AND realm_id = ? ORDER BY ts DESC LIMIT 1
        """

        values = (event_id, realm_id)

        res = self.execute_query(query, values)

        townhall_summary: str | None = res[0][0] if len(res) > 0 else None
        return townhall_summary
