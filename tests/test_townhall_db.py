import pytest

from overlore.sqlite.townhall_db import TownhallDatabase
from tests.utils.townhall_db_test_utils import (
    format_townhalls,
    generate_plotlines,
    generate_townhalls_for_realmid,
    given_plots,
    given_thoughts,
    given_townhall_values,
    given_townhall_values_for_single_realm,
    given_update_plots,
)


@pytest.fixture
def db():
    db = TownhallDatabase.instance().init(":memory:")
    yield db
    db.close_conn()


def test_insert_and_fetch_townhall_discussion(db):
    for item in given_townhall_values:
        added_rowid = db.insert_townhall_discussion(item["realm_id"], item["discussion"], item["input"])
        retrieved_entry = db.fetch_realm_townhalls(item["realm_id"])[0]

        assert added_rowid == item["rowid"], f"Expected rowid {item['rowid']}, got {added_rowid}"
        assert retrieved_entry == (
            item["discussion"],
            item["input"],
        ), f"Expected profile '{(item['discussion'], item['input'])}', got '{retrieved_entry}'"


def test_fetch_multiple_townhalls(db):
    realm_id = 999
    generate_townhalls_for_realmid(db, realm_id, given_townhall_values_for_single_realm)

    retrieved_entries = db.fetch_realm_townhalls(realm_id)

    assert retrieved_entries == format_townhalls(
        given_townhall_values_for_single_realm
    ), f"Failed to fetch all townhalls for realm_id {realm_id}"


def test_insert_and_fetch_plot(db):
    for item in given_plots:
        added_rowid = db.insert_plotline(item["realm_id"], item["plot"])
        retrieved_entry = db.fetch_plotline_by_realm(item["realm_id"])

        assert added_rowid == item["rowid"], f"Expected rowid {item['rowid']}, got {added_rowid}"
        assert retrieved_entry == item["plot"], f"Expected plot '{item['plot']}', got '{retrieved_entry}'"


def test_update_plot(db):
    generate_plotlines(db)

    for item in given_update_plots:
        update_count = db.update_plotline(item["realm_id"], item["new_plot"])
        retrieved_entry = db.fetch_plotline_by_realm(item["realm_id"])

        assert update_count == 1, f"Expected update count 1, got {update_count}"
        assert retrieved_entry == item["new_plot"], f"Expected plot '{item['new_plot']}', got '{retrieved_entry}'"


def test_delete_plotline(db):
    generate_plotlines(db)

    for item in given_plots:
        db.delete_plotline(item["realm_id"])
        residual_entry = db.fetch_plotline_by_realm(item["realm_id"])

        assert residual_entry == "", "plot entry was not deleted"


def test_insert_and_fetch_npc_thought(db):
    for item in given_thoughts:
        added_rowid = db.insert_npc_thought(item["npc_entity_id"], item["thought"], item["embedding"])
        retrieved_entry = db.fetch_npc_thought(added_rowid)

        assert added_rowid == item["rowid"], f"Expected rowid {item['rowid']}, got {added_rowid}"
        assert retrieved_entry == item["thought"], f"Expected thought '{item['thought']}', got '{retrieved_entry}'"
