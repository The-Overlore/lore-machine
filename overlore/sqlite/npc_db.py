from __future__ import annotations

import logging
from sqlite3 import Connection
from typing import cast

from overlore.sqlite.base_db import BaseDatabase
from overlore.sqlite.constants import Profile
from overlore.types import NpcProfile, ParsedSpawnEvent

logger = logging.getLogger("overlore")


class NpcDatabase(BaseDatabase):
    _instance: NpcDatabase | None = None

    EXTENSIONS: list[str] = []
    FIRST_BOOT_QUERIES: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS npc_spawn (
                realm_entity_id INTEGER NOT NULL,
                full_name TEXT,
                age INTEGER,
                role INTEGER,
                sex INTEGER,
                trait TEXT,
                description TEXT
            );
        """,
        """
            CREATE TABLE IF NOT EXISTS npc_info (
                npc_id INTEGER NOT NULL,
                description TEXT
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

    def init(self, path: str = "./databases/npc_spawn.db") -> NpcDatabase:
        # Call parent init function
        self._init(
            path,
            self.EXTENSIONS,
            self.FIRST_BOOT_QUERIES,
            [],
            self._preload,
        )
        return self

    def get_all_npc_spawn(self) -> list[NpcProfile]:
        return self.execute_query("SELECT * FROM npc_spawn", ())

    def get_all_npc_info(self) -> list[NpcProfile]:
        return self.execute_query("SELECT * FROM npc_info", ())

    def insert_npc_spawn(self, realm_entity_id: int, npc: NpcProfile) -> int:
        query = (
            "INSERT INTO npc_spawn(realm_entity_id, full_name, age, role, sex, trait, description) VALUES (?, ?, ?, ?,"
            " ?, ?, ?)"
        )
        values = (
            realm_entity_id,
            npc["full_name"],  # type: ignore[index]
            npc["characteristics"]["age"],  # type: ignore[index]
            npc["characteristics"]["role"],  # type: ignore[index]
            npc["characteristics"]["sex"],  # type: ignore[index]
            npc["character_trait"],  # type: ignore[index]
            npc["description"],  # type: ignore[index]
        )
        row_id = self._insert(query, values)

        logger.info(f"Stored npc_spawn entry at rowid {row_id} for realm_entity_id {realm_entity_id}")
        return row_id

    def insert_npc_info(self, npc_id: int, description: str) -> int:
        row_id = self._insert("INSERT INTO npc_info(npc_id, description) VALUES (?, ?)", (npc_id, description))
        return row_id

    def fetch_npc_spawn_by_realm(self, realm_entity_id: int) -> NpcProfile | None:
        profile = self.execute_query("SELECT * FROM npc_spawn WHERE realm_entity_id = ?", (realm_entity_id,))
        if profile == []:
            return None
        else:
            profile = profile[0]
            return cast(
                NpcProfile,
                {
                    "character_trait": profile[Profile.TRAIT.value],
                    "characteristics": {
                        "age": cast(int, profile[Profile.AGE.value]),
                        "role": cast(int, profile[Profile.ROLE.value]),
                        "sex": cast(int, profile[Profile.SEX.value]),
                    },
                    "full_name": profile[Profile.FULL_NAME.value],
                    "description": profile[Profile.DESCRIPTION.value],
                },
            )

    def fetch_npc_info(self, npc_id: int) -> str | None:
        description = self.execute_query("SELECT description FROM npc_info WHERE npc_id = ?", (npc_id,))
        if description != []:
            return str(description[0][0])
        return None

    def delete_npc_spawn_by_realm(self, event: ParsedSpawnEvent) -> None:
        realm_entity_id = event["realm_entity_id"]
        npc_entity_id = event["npc_entity_id"]

        description = self.execute_query(
            "SELECT description FROM npc_spawn WHERE realm_entity_id == (?)", (realm_entity_id,)
        )
        if description != []:
            self.insert_npc_info(npc_entity_id, str(description[0][0]))

        start_count = len(self.get_all_npc_spawn())
        self.execute_query("DELETE FROM npc_spawn WHERE realm_entity_id == (?)", (realm_entity_id,))
        end_count = len(self.get_all_npc_spawn())

        if end_count < start_count:
            logger.info(f"Deleted npc_spawn entry for realm_entity_id {realm_entity_id}")
        else:
            logger.info(f"Failed to delete npc_spawn entry for realm_entity_id {realm_entity_id}")
