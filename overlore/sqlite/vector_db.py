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
        query = "SELECT * FROM townhall"
        records = self.execute_query(query, ())

        vss_query = "SELECT * FROM vss_townhall"
        records_vss = self.execute_query(vss_query, ())

        return len(records), len(records_vss)

    def insert_townhall_discussion(
        self, discussion: str, summary: str, realm_id: int, event_ids: list[int], embedding: list[float]
    ) -> None:
        discussion = discussion.strip()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rowid = self._insert(
            "INSERT INTO townhall (discussion, summary, realm_id, events_ids, ts) VALUES (?, ?, ?, ?, ?);",
            (discussion, summary, realm_id, json.dumps(event_ids), ts),
        )
        self._insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))

    def query_nearest_neighbour(self, query_embedding: str, realm_id: int, limit: int = 1) -> list[StoredVector]:
        # Use vss_search for SQLite version < 3.41 else vss_search_params db function
        query = """
            select v.rowid, v.distance from vss_townhall v
            inner join townhall t on v.rowid = t.rowid
            where t.realm_id = ? and vss_search(embedding, vss_search_params(?, ?))
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

    def get_townhalls_from_events(self, event_ids: list[int]) -> tuple[list[str], list[int]]:
        """
        Returns tuple of:
            - List of townhalls summary. One event_id of the list given in parameter must have been involved in the generation of the discussion.
            - Events_ids in the list given in parameter which haven't generated any summary before
        """
        event_ids.extend([0 for i in range(0, 5 - len(event_ids))])

        query = """
            WITH GivenEventIDs(event_id) AS (VALUES (?), (?), (?), (?), (?)),
            RecentDiscussions AS (
                SELECT
                    json_each.value AS event_id,
                    T.summary,
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
                    summary,
                    rowid,
                    ROW_NUMBER() OVER (PARTITION BY rowid ORDER BY ts DESC) as dup_rn
                FROM
                    RecentDiscussions
                WHERE
                    rn = 1
            )
            SELECT
                event_id,
                summary
            FROM
                DupDiscussions
            WHERE
                dup_rn = 1
            UNION ALL
            SELECT
                event_id,
                NULL AS summary
            FROM
                GivenEventIDs
            WHERE
                event_id NOT IN (SELECT event_id FROM RecentDiscussions WHERE rn = 1)
        """
        values = (
            event_ids[0],
            event_ids[1],
            event_ids[2],
            event_ids[3],
            event_ids[4],
            event_ids[0],
            event_ids[1],
            event_ids[2],
            event_ids[3],
            event_ids[4],
        )

        # list of tuples: either (event_id, discussion) or (event_id, None) if the event_id hasn't generated and discussion before
        res = self.execute_query(query, values)
        townhall_summaries: list[str] = [item[1] for item in res if item[1] is not None]
        event_ids_previously_unused: list[int] = [item[0] for item in res if item[1] is None]

        return (townhall_summaries, event_ids_previously_unused)
