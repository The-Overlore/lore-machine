from __future__ import annotations

import logging
from sqlite3 import Connection
from typing import cast

from overlore.eternum.types import Npc
from overlore.sqlite.db import Database
from overlore.sqlite.types import StoredNpcProfile

logger = logging.getLogger("overlore")


class NpcDatabase(Database):
    _instance: NpcDatabase | None = None

    EXTENSIONS: list[str] = []
    FIRST_BOOT_QUERIES: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS npc_spawn (
                realm_id INTEGER NOT NULL,
                name TEXT,
                sex INTEGER,
                role INTEGER,
                trait TEXT,
                summary TEXT
            );
        """,
        """
            CREATE TABLE IF NOT EXISTS npc_info (
                npc_id INTEGER NOT NULL,
                summary TEXT
            );
        """,
    ]

    @classmethod
    def instance(cls) -> NpcDatabase:
        if cls._instance is None:
            logger.debug("Creating npc_spawn db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def _preload(self, db: Connection) -> None:
        # noop
        pass

    def init(self, path: str = "./npc_spawn.db") -> NpcDatabase:
        # Call parent init function
        self._init(
            path,
            self.EXTENSIONS,
            self.FIRST_BOOT_QUERIES,
            [],
            self._preload,
        )
        return self

    def get_all_npc_spawn(self) -> list[Npc]:
        return self.execute_query("SELECT * FROM npc_spawn", ())

    def get_all_npc_info(self) -> list[Npc]:
        return self.execute_query("SELECT * FROM npc_info", ())

    def insert_npc_spawn(self, realm_id: int, npc: Npc) -> int:
        query = "INSERT INTO npc_spawn(realm_id, name, sex, role, trait, summary) VALUES (?, ?, ?, ?, ?, ?)"
        values = (
            realm_id,
            npc["fullName"],
            cast(int, npc["sex"]),
            cast(int, npc["role"]),
            npc["characterTrait"],
            npc["description"],
        )
        row_id = self._insert(query, values)

        logger.info(f"Stored npc_spawn entry at rowid {row_id} for realm_id {realm_id}")
        return row_id

    def insert_npc_info(self, npc_id: int, summary: str) -> None:
        self._insert("INSERT INTO npc_info(npc_id, summary) VALUES (?, ?)", (npc_id, summary))

    def fetch_npc_spawn_by_realm(self, realm_id: int) -> StoredNpcProfile | None:
        res = self.execute_query("SELECT * FROM npc_spawn WHERE realm_id = ?", (realm_id,))
        if res == []:
            return None
        else:
            return tuple(res[0])

    def fetch_npc_info(self, npc_id: int) -> str | None:
        summary = self.execute_query("SELECT summary FROM npc_info WHERE npc_id = ?", (npc_id,))
        if summary != []:
            return str(summary[0][0])
        return None

    def delete_npc_spawn_by_realm(self, realm_id: int, npc_id: int) -> None:
        summary = self.execute_query("SELECT summary FROM npc_spawn WHERE realm_id == (?)", (realm_id,))
        if summary != []:
            self.insert_npc_info(npc_id, str(summary[0][0]))

        start_count = len(self.get_all_npc_spawn())
        self.execute_query("DELETE FROM npc_spawn WHERE realm_id == (?)", (realm_id,))
        end_count = len(self.get_all_npc_spawn())

        if end_count < start_count:
            logger.info(f"Deleted npc_spawn entry for realm_id {realm_id}")
        else:
            logger.info(f"Failed to delete npc_spawn entry for realm_id {realm_id}")
