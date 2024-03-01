import pytest

from overlore.eternum.types import Npc
from overlore.sqlite.npc_db import NpcDatabase


class Profile:
    "REALMID = 0,AGE = 1, NAME = 2, SEX = 3, TRAIT = 4, SUMMARY = 5"
    REALMID = 0
    NAME = 1
    SEX = 2
    TRAIT = 3
    SUMMARY = 4


DATA: list[Npc] = [
    {"fullName": "Luke Luke", "sex": 0, "role": 1, "characterTrait": "Assertive", "description": "Short summary"},
    {"fullName": "Bobby Bob", "sex": 1, "role": 2, "characterTrait": "Submissive", "description": "Short summary"},
    {"fullName": "Lenny Len", "sex": 0, "role": 3, "characterTrait": "Happy", "description": "Short summary"},
]


@pytest.mark.asyncio
async def test_create_and_read_entry():
    db = NpcDatabase.instance().init(":memory:")

    assert None is db.fetch_npc_spawn_by_realm(1)

    assert db.insert_npc_spawn(1, DATA[0]) == 1
    assert (1, "Luke Luke", 0, 1, "Assertive", "Short summary") == db.fetch_npc_spawn_by_realm(1)

    assert db.insert_npc_spawn(2, DATA[1]) == 2
    assert (2, "Bobby Bob", 1, 2, "Submissive", "Short summary") == db.fetch_npc_spawn_by_realm(2)

    assert None is db.fetch_npc_spawn_by_realm(100)
    assert None is db.fetch_npc_spawn_by_realm(0)
    assert None is db.fetch_npc_spawn_by_realm(-100)


@pytest.mark.asyncio
async def test_delete_entry():
    db = NpcDatabase.instance().init(":memory:")

    db.insert_npc_spawn(1, DATA[0])
    assert len(db.get_all_npc_spawn()) == 1
    db.delete_npc_spawn_by_realm(1, 1)
    assert len(db.get_all_npc_spawn()) == 0
    assert db.fetch_npc_info(1) == "Short summary"
    assert len(db.get_all_npc_info()) == 1

    db.insert_npc_spawn(1, DATA[0])
    db.insert_npc_spawn(2, DATA[1])
    db.insert_npc_spawn(3, DATA[2])
    assert len(db.get_all_npc_spawn()) == 3
