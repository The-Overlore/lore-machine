from __future__ import annotations

import logging
from sqlite3 import Connection
from typing import cast

from overlore.sqlite.base_db import BaseDatabase
from overlore.sqlite.constants import Profile
from overlore.sqlite.errors import NpcDescriptionNotFoundError, NpcProfileNotDeleted
from overlore.types import NpcProfile

logger = logging.getLogger("overlore")


class NpcDatabase(BaseDatabase):
    _instance: NpcDatabase | None = None

    EXTENSIONS: list[str] = []
    FIRST_BOOT_QUERIES: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS npc_profile (
                realm_entity_id INTEGER NOT NULL,
                full_name TEXT,
                age INTEGER,
                role INTEGER,
                sex INTEGER,
                character_trait TEXT,
                description TEXT
            );
        """,
        """
            CREATE TABLE IF NOT EXISTS npc_description (
                npc_entity_id INTEGER NOT NULL,
                description TEXT
            );
        """,
    ]

    @classmethod
    def instance(cls) -> NpcDatabase:
        if cls._instance is None:
            logger.debug("Creating npc db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def _preload(self, db: Connection) -> None:
        pass

    def init(self, path: str = "./databases/npc.db") -> NpcDatabase:
        self._init(
            path,
            self.EXTENSIONS,
            self.FIRST_BOOT_QUERIES,
            [],
            self._preload,
        )
        return self

    def insert_npc_profile(self, realm_entity_id: int, npc: NpcProfile) -> int:
        added_row_id = self._insert(
            "INSERT INTO npc_profile(realm_entity_id, full_name, age, role, sex, character_trait, description) VALUES"
            " (?, ?, ?, ?, ?, ?, ?);",
            (
                realm_entity_id,
                npc["full_name"],  # type: ignore[index]
                npc["characteristics"]["age"],  # type: ignore[index]
                npc["characteristics"]["role"],  # type: ignore[index]
                npc["characteristics"]["sex"],  # type: ignore[index]
                npc["character_trait"],  # type: ignore[index]
                npc["description"],  # type: ignore[index]
            ),
        )
        return added_row_id

    def fetch_npc_profile_by_realm_entity_id(self, realm_entity_id: int) -> NpcProfile | None:
        profile = self.execute_query("SELECT * FROM npc_profile WHERE realm_entity_id = ?;", (realm_entity_id,))

        if not profile:
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

    def fetch_npc_description(self, npc_entity_id: int) -> str:
        description = self.execute_query(
            "SELECT description FROM npc_description WHERE npc_entity_id = ?;", (npc_entity_id,)
        )

        if not description:
            raise NpcDescriptionNotFoundError(f"No NPC description found at npc_entity_id {npc_entity_id}")
        return str(description[0][0])

    def insert_npc_description(self, npc_entity_id: int, realm_entity_id: int) -> int:
        description = self.execute_query(
            "SELECT description FROM npc_profile WHERE realm_entity_id = ?;", (realm_entity_id,)
        )

        if not description:
            raise NpcDescriptionNotFoundError(f"No NPC description found at npc_entity_id {npc_entity_id}")

        row_id = self._insert(
            "INSERT INTO npc_description (npc_entity_id, description) VALUES (?, ?);",
            (npc_entity_id, description[0][0]),
        )
        return row_id

    def delete_npc_profile_by_realm_entity_id(self, realm_entity_id: int) -> None:
        self._delete("DELETE FROM npc_profile WHERE realm_entity_id = ?;", (realm_entity_id,))

    def verify_npc_profile_is_deleted(self, realm_entity_id: int) -> None:
        profile = self.execute_query("SELECT * FROM npc_profile WHERE realm_entity_id = ?;", (realm_entity_id,))

        if profile:
            raise NpcProfileNotDeleted(f"Found npc profile for realm_entity_id {realm_entity_id}")
