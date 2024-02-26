import pytest

from overlore.sqlite.constants import Profile
from overlore.sqlite.npc_spawn_db import NpcSpawnDatabase
from overlore.sqlite.types import StoredNpcProfile

DATA: list[StoredNpcProfile] = [
    (1, "Luke Luke", "Male", "Assertive", "Short summary"),
    (2, "Bobby Bob", "Female", "Submissive", "Short summary"),
    (3, "Lenny Len", "Male", "Happy", "Short summary"),
]


def empty_str_at_index(npc: StoredNpcProfile, index: int) -> StoredNpcProfile:
    npc_list = list(npc)
    npc_list[index] = ""
    return tuple(npc_list)


def negative_number_at_index(npc: StoredNpcProfile, index: int) -> StoredNpcProfile:
    npc_list = list(npc)
    npc_list[index] = -100
    return tuple(npc_list)


@pytest.mark.asyncio
async def test_create_and_read_entry():
    db = NpcSpawnDatabase.instance().init(":memory:")

    assert None is db.fetch_npc_spawn_by_realm(DATA[0][Profile.REALMID.value])

    assert db.insert_npc_spawn(DATA[0]) == 1
    assert (1, "Luke Luke", "Male", "Assertive", "Short summary") == db.fetch_npc_spawn_by_realm(
        DATA[0][Profile.REALMID.value]
    )

    with pytest.raises(ValueError):
        db.insert_npc_spawn(DATA[0])
    assert len(db.get_all()) == 1

    assert db.insert_npc_spawn(DATA[1]) == 2
    assert (2, "Bobby Bob", "Female", "Submissive", "Short summary") == db.fetch_npc_spawn_by_realm(
        DATA[1][Profile.REALMID.value]
    )

    with pytest.raises(ValueError):
        db.insert_npc_spawn(DATA[1])
    assert len(db.get_all()) == 2

    assert None is db.fetch_npc_spawn_by_realm(100)
    assert None is db.fetch_npc_spawn_by_realm(0)
    assert None is db.fetch_npc_spawn_by_realm(-100)

    with pytest.raises(ValueError):
        db.insert_npc_spawn(empty_str_at_index(DATA[2], Profile.NAME.value))
    with pytest.raises(ValueError):
        db.insert_npc_spawn(empty_str_at_index(DATA[2], Profile.SEX.value))
    with pytest.raises(ValueError):
        db.insert_npc_spawn(empty_str_at_index(DATA[2], Profile.TRAIT.value))
    with pytest.raises(ValueError):
        db.insert_npc_spawn(empty_str_at_index(DATA[2], Profile.SUMMARY.value))


@pytest.mark.asyncio
async def test_delete_entry():
    db = NpcSpawnDatabase.instance().init(":memory:")

    db.insert_npc_spawn(DATA[0])
    assert len(db.get_all()) == 1
    db.remove_npc_spawn_by_realm(DATA[0][Profile.REALMID.value])
    assert len(db.get_all()) == 0

    db.insert_npc_spawn(DATA[0])
    db.insert_npc_spawn(DATA[1])
    db.insert_npc_spawn(DATA[2])
    assert len(db.get_all()) == 3

    db.remove_npc_spawn_by_realm(DATA[0][Profile.REALMID.value])
    assert len(db.get_all()) == 2
    db.remove_npc_spawn_by_realm(DATA[0][Profile.REALMID.value])
    assert len(db.get_all()) == 2
