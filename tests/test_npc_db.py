import pytest

from overlore.sqlite.npc_db import NpcDatabase
from overlore.types import Characteristics, Npc

DATA: list[Npc] = [
    {
        "full_name": "Luke Luke",
        "characteristics": {"age": 33, "sex": 0, "role": 1},
        "character_trait": "Assertive",
        "description": "Short summary",
    },
    {
        "full_name": "Bobby Bob",
        "characteristics": {"age": 28, "sex": 1, "role": 2},
        "character_trait": "Submissive",
        "description": "Short summary",
    },
    {
        "full_name": "Lenny Len",
        "characteristics": {"age": 16, "sex": 0, "role": 3},
        "character_trait": "Happy",
        "description": "Short summary",
    },
]


@pytest.mark.asyncio
async def test_create_and_read_entry():
    db = NpcDatabase.instance().init(":memory:")

    assert None is db.fetch_npc_spawn_by_realm(1)

    assert db.insert_npc_spawn(1, DATA[0]) == 1

    assert Npc(
        character_trait="Assertive",
        characteristics=Characteristics(
            age=33,
            role=1,
            sex=0,
        ),
        full_name="Luke Luke",
        description="Short summary",
    ) == db.fetch_npc_spawn_by_realm(1)

    assert db.insert_npc_spawn(2, DATA[1]) == 2

    assert Npc(
        character_trait="Submissive",
        characteristics=Characteristics(
            age=28,
            role=2,
            sex=1,
        ),
        full_name="Bobby Bob",
        description="Short summary",
    ) == db.fetch_npc_spawn_by_realm(2)

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
