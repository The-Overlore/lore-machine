import pytest

from overlore.sqlite.errors import NpcDescriptionNotFoundError, NpcProfileNotFoundError
from overlore.sqlite.npc_db import NpcDatabase
from tests.utils.npc_db_test_utils import given_insert_values, insert_data_into_db


@pytest.fixture
def db():
    db = NpcDatabase.instance().init(":memory:")
    yield db
    db.close_conn()


def test_insert_and_fetch_spawn_npc(db):
    for item in given_insert_values:
        added_rowid = db.insert_npc_spawn(item["realm_entity_id"], item["profile"])
        retrieved_entry = db.fetch_npc_spawn_by_realm(item["realm_entity_id"])

        assert added_rowid == item["rowid"], f"Expected rowid {item['rowid']}, got {added_rowid}"
        assert retrieved_entry == item["profile"], f"Expected profile '{item['profile']}', got '{retrieved_entry}'"


def test_insert_and_fetch_spawn_info(db):
    insert_data_into_db(db)

    for item in given_insert_values:
        added_rowid = db.insert_npc_info(item["npc_entity_id"], item["realm_entity_id"])
        retrieved_entry = db.fetch_npc_info(item["npc_entity_id"])

        assert added_rowid == item["rowid"], f"Expected rowid {item['rowid']}, got {added_rowid}"
        assert (
            retrieved_entry == item["profile"]["description"]
        ), f"Expected description '{item['profile']['description']}', got '{retrieved_entry}'"


def test_delete_spawn_npc_profile(db):
    insert_data_into_db(db)

    for item in given_insert_values:
        db.delete_npc_spawn_by_realm(item["realm_entity_id"])
        residual_entry = db.execute_query(
            "SELECT rowid FROM npc_spawn WHERE realm_entity_id = ?;", (item["realm_entity_id"],)
        )

        assert residual_entry == [], "Spawn npc entry was not deleted"


def test_fetch_spawn_npc_not_found_error(db):
    with pytest.raises(NpcProfileNotFoundError):
        db.fetch_npc_spawn_by_realm(999)


def test_fetch_npc_description_not_found_error(db):
    with pytest.raises(NpcDescriptionNotFoundError):
        db.fetch_npc_info(999)
