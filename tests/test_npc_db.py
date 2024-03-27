import pytest

from overlore.sqlite.errors import NpcDescriptionNotFoundError, NpcProfileNotFoundError
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


def test_insert_and_fetch_npc_description(db):
    prepare_data(db)

    for item in test_data:
        added_row_id = db.insert_npc_description(item["npc_entity_id"], item["realm_entity_id"])
        retrieved_entry = db.fetch_npc_description(item["npc_entity_id"])

        assert added_row_id == item["rowid"], f"Expected rowid {item['rowid']}, got {added_row_id}"
        assert (
            retrieved_entry == item["profile"]["description"]
        ), f"Expected description '{item['profile']['description']}', got '{retrieved_entry}'"


def test_delete_npc_profile(db):
    prepare_data(db)

    for item in test_data:
        db.delete_npc_profile_by_realm_entity_id(item["realm_entity_id"])

        residual_entry = db.fetch_npc_profile_by_realm_entity_id(item["realm_entity_id"])

        assert len(residual_entry) == 0, "Npc profile entry was not deleted"


def test_fetch_npc_profile_not_found_error(db):
    with pytest.raises(NpcProfileNotFoundError):
        db.fetch_npc_profile_by_realm_entity_id(999)


def test_fetch_npc_description_not_found_error(db):
    with pytest.raises(NpcDescriptionNotFoundError):
        db.fetch_npc_description(999)
