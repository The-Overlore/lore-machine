from __future__ import annotations

import logging
from sqlite3 import Connection
from typing import cast

from overlore.sqlite.base_db import BaseDatabase
from overlore.sqlite.constants import Profile
from overlore.sqlite.errors import NpcDescriptionNotFoundError, NpcProfileNotDeleted
from overlore.types import Backstory, Characteristics, NpcProfile

logger = logging.getLogger("overlore")


class NpcDatabase(BaseDatabase):
    _instance: NpcDatabase | None = None

    EXTENSIONS: list[str] = []
    MIGRATIONS: list[str] = [
        """
            CREATE TABLE IF NOT EXISTS npc_profile (
                realm_entity_id INTEGER NOT NULL,
                full_name TEXT,
                age INTEGER,
                role INTEGER,
                sex INTEGER,
                character_trait TEXT,
                backstory TEXT,
                backstory_poignancy INT
            );
        """,
        """
            CREATE TABLE IF NOT EXISTS npc_backstory (
                npc_entity_id INTEGER NOT NULL,
                backstory TEXT,
                poignancy INT
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
            self.MIGRATIONS,
            [],
            self._preload,
        )
        return self

    def insert_npc_profile(self, realm_entity_id: int, npc: NpcProfile) -> int:
        added_row_id = self._insert(
            "INSERT INTO npc_profile(realm_entity_id, full_name, age, role, sex, character_trait, backstory,"
            " backstory_poignancy) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (
                realm_entity_id,
                npc.full_name,
                npc.characteristics.age,
                npc.characteristics.role,
                npc.characteristics.sex,
                npc.character_trait,
                npc.backstory.backstory,
                npc.backstory.poignancy,
            ),
        )
        return added_row_id

    def fetch_npc_profile_by_realm_entity_id(self, realm_entity_id: int) -> NpcProfile | None:
        profile = self.execute_query("SELECT * FROM npc_profile WHERE realm_entity_id = ?;", (realm_entity_id,))

        if not profile:
            return None
        else:
            profile = profile[0]

            return NpcProfile(
                character_trait=profile[Profile.TRAIT.value],
                characteristics=Characteristics(
                    age=cast(int, profile[Profile.AGE.value]),
                    role=cast(int, profile[Profile.ROLE.value]),
                    sex=cast(int, profile[Profile.SEX.value]),
                ),
                full_name=profile[Profile.FULL_NAME.value],
                backstory=Backstory(
                    backstory=profile[Profile.BACKSTORY.value], poignancy=profile[Profile.BACKSTORY_POIGNANCY.value]
                ),
            )

    def fetch_npc_backstory(self, npc_entity_id: int) -> Backstory:
        backstory = self.execute_query(
            "SELECT backstory, poignancy FROM npc_backstory WHERE npc_entity_id = ?;", (npc_entity_id,)
        )

        if not backstory:
            raise NpcDescriptionNotFoundError(f"No villager backstory found at npc_entity_id {npc_entity_id}")
        return Backstory(backstory=backstory[0][0], poignancy=backstory[0][1])

    def fetch_npcs_backstories(self, npc_entity_ids: list[int]) -> list[tuple[int, str]]:
        query = (
            "SELECT npc_entity_id, backstory FROM npc_backstory WHERE npc_entity_id IN"
            f" ({','.join(['?'] * len(npc_entity_ids))});"
        )
        params = tuple(npc_entity_ids)
        ret = self.execute_query(query=query, params=params)
        return ret

    def insert_npc_backstory(self, npc_entity_id: int, realm_entity_id: int) -> int:
        backstory = self.execute_query(
            "SELECT backstory, backstory_poignancy FROM npc_profile WHERE realm_entity_id = ?;", (realm_entity_id,)
        )

        if not backstory:
            raise NpcDescriptionNotFoundError(f"No villager backstory found at npc_entity_id {npc_entity_id}")

        back_story: str = backstory[0][0]
        poignancy: int = backstory[0][1]

        row_id = self._insert(
            "INSERT INTO npc_backstory (npc_entity_id, backstory, poignancy) VALUES (?, ?, ?);",
            (npc_entity_id, back_story, poignancy),
        )
        return row_id

    def delete_npc_profile_by_realm_entity_id(self, realm_entity_id: int) -> None:
        self._delete("DELETE FROM npc_profile WHERE realm_entity_id = ?;", (realm_entity_id,))

    def verify_npc_profile_is_deleted(self, realm_entity_id: int) -> None:
        profile = self.execute_query("SELECT * FROM npc_profile WHERE realm_entity_id = ?;", (realm_entity_id,))

        if profile:
            raise NpcProfileNotDeleted(f"Found npc profile for realm_entity_id {realm_entity_id}")
