import pytest

from overlore.sqlite.errors import NpcDescriptionNotFoundError
from overlore.sqlite.npc_db import NpcDatabase
from tests.utils.npc_db_test_utils import prepare_data, test_data


@pytest.fixture
def db():
    db = NpcDatabase.instance().init(":memory:")
    yield db
    db.close_conn()


def test_insert_and_fetch_npc_profile(db):
    for item in test_data:
        added_row_id = db.insert_npc_profile(item["realm_entity_id"], item["profile"])
        retrieved_entry = db.fetch_npc_profile_by_realm_entity_id(item["realm_entity_id"])

        assert added_row_id == item["rowid"], f"Expected rowid {item['rowid']}, got {added_row_id}"
        assert retrieved_entry == item["profile"], f"Expected profile '{item['profile']}', got '{retrieved_entry}'"


def test_insert_and_fetch_npc_backstory(db):
    prepare_data(db)

    for item in test_data:
        added_row_id = db.insert_npc_backstory(item["npc_entity_id"], item["realm_entity_id"])
        retrieved_entry = db.fetch_npc_backstory(item["npc_entity_id"])

        assert added_row_id == item["rowid"], f"Expected rowid {item['rowid']}, got {added_row_id}"
        assert (
            retrieved_entry == item["profile"]["backstory"]
        ), f"Expected backstory '{item['profile']['backstory']}', got '{retrieved_entry}'"


def test_delete_npc_profile(db):
    prepare_data(db)

    for item in test_data:
        db.delete_npc_profile_by_realm_entity_id(item["realm_entity_id"])

        assert None is db.fetch_npc_profile_by_realm_entity_id(item["realm_entity_id"])


def test_fetch_npc_profile_not_found_error(db):
    assert None is db.fetch_npc_profile_by_realm_entity_id(INVALID_NPC_ENTITY_ID)


def test_fetch_npc_backstory_not_found_error(db):
    with pytest.raises(NpcDescriptionNotFoundError):
        db.fetch_npc_backstory(INVALID_NPC_ENTITY_ID)


INVALID_NPC_ENTITY_ID = 999
