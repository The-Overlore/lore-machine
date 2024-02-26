from __future__ import annotations

import logging
from sqlite3 import Connection

from overlore.sqlite.constants import Profile
from overlore.sqlite.db import Database
from overlore.sqlite.types import StoredNpcProfile

logger = logging.getLogger("overlore")


class NpcSpawnDatabase(Database):
    _instance: NpcSpawnDatabase | None = None

    EXTENSIONS: list[str] = []
    FIRST_BOOT_QUERIES: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS npc_spawn (
                realm_id INTEGER NOT NULL,
                name TEXT,
                sex TEXT,
                trait TEXT,
                summary TEXT
            );
        """
    ]

    @classmethod
    def instance(cls) -> NpcSpawnDatabase:
        if cls._instance is None:
            logger.debug("Creating npc_spawn db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def _preload(self, db: Connection) -> None:
        # noop
        pass

    def init(self, path: str = "./npc_spawn.db") -> NpcSpawnDatabase:
        # Call parent init function
        self._init(
            path,
            self.EXTENSIONS,
            self.FIRST_BOOT_QUERIES,
            [],
            self._preload,
        )
        return self

    def get_all(self) -> list[StoredNpcProfile]:
        return self.execute_query("SELECT * FROM npc_spawn", ())

    def insert_npc_spawn(self, npc: StoredNpcProfile) -> int:
        if self.fetch_npc_spawn_by_realm(npc[Profile.REALMID.value]) is not None:
            raise ValueError(f"Existing entry found for realm {npc[Profile.REALMID.value]}")
        if not all(
            npc[index] != ""
            for index in [
                Profile.NAME.value,
                Profile.SEX.value,
                Profile.TRAIT.value,
                Profile.SUMMARY.value,
            ]
        ):
            raise ValueError("Found empty field in npc profile")

        row_id = self._insert("INSERT INTO npc_spawn(realm_id, name, sex, trait, summary) VALUES (?, ?, ?, ?, ?)", npc)

        logger.info(f"Stored npc_spawn entry at rowid {row_id} for realm_id {npc[Profile.REALMID.value]}")
        return row_id

    def fetch_npc_spawn_by_realm(self, realm_id: int) -> StoredNpcProfile | None:
        res = self.execute_query("SELECT * FROM npc_spawn WHERE realm_id = ?", (realm_id,))
        if res == []:
            return None
        else:
            return tuple(res[0])

    def remove_npc_spawn_by_realm(self, realm_id: int) -> None:
        start_count = self.get_all()
        self.execute_query("DELETE FROM npc_spawn WHERE realm_id == (?)", (realm_id,))
        end_count = self.get_all()
        if end_count < start_count:
            logger.info(f"Deleted npc_spawn entry for realm_id {realm_id}")
        else:
            logger.info(f"Could not find npc_spawn entry for realm {realm_id} to delete")
