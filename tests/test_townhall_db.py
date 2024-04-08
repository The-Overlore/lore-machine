import pytest

from overlore.sqlite.townhall_db import TownhallDatabase
from tests.utils.townhall_db_test_utils import (
    dtt_test_data,
    format_townhalls,
    generate_townhalls_for_realmid,
    given_thoughts,
    given_townhall_values,
    given_townhall_values_for_single_realm,
    prepare_data_dtt,
)


@pytest.fixture
def db():
    db = TownhallDatabase.instance().init(":memory:")
    yield db
    db.close_conn()


def test_insert_and_fetch_townhall_discussion(db):
    for item in given_townhall_values:
        added_row_id = db.insert_townhall_discussion(item["realm_id"], item["discussion"], item["input"], item["ts"])
        retrieved_entry = db.fetch_townhalls_by_realm_id(item["realm_id"])[0]

        assert added_row_id == item["rowid"], f"Expected rowid {item['rowid']}, got {added_row_id}"
        assert retrieved_entry == (
            item["discussion"],
            item["input"],
        ), f"Expected profile '{(item['discussion'], item['input'])}', got '{retrieved_entry}'"


def test_fetch_multiple_townhalls(db):
    realm_id = 999
    generate_townhalls_for_realmid(db, realm_id, given_townhall_values_for_single_realm)

    retrieved_entries = db.fetch_townhalls_by_realm_id(realm_id)

    assert retrieved_entries == format_townhalls(
        given_townhall_values_for_single_realm
    ), f"Failed to fetch all townhalls for realm_id {realm_id}"


def test_insert_and_fetch_npc_thought(db):
    for item in given_thoughts:
        added_row_id = db.insert_npc_thought(item["npc_entity_id"], item["thought"], item["embedding"])
        retrieved_entry = db.fetch_npc_thought_by_row_id(added_row_id)

        assert added_row_id == item["rowid"], f"Expected rowid {item['rowid']}, got {added_row_id}"
        assert retrieved_entry == item["thought"], f"Expected thought '{item['thought']}', got '{retrieved_entry}'"


def test_insert_and_fetch_daily_townhall_tracker(db):
    for item in dtt_test_data:
        added_row_id = db.insert_or_update_daily_townhall_tracker(item["realm_id"], item["event_row_id"])

        assert item["row_id"] == added_row_id
        assert [item["event_row_id"]] == db.fetch_daily_townhall_tracker(item["realm_id"])


def test_update_daily_townhall_tracker(db):
    row_ids = []
    for item in dtt_test_data:
        updated_count = db.insert_or_update_daily_townhall_tracker(1, item["event_row_id"])
        row_ids.append(item["event_row_id"])

        assert updated_count == 1
        assert row_ids == db.fetch_daily_townhall_tracker(1)


def delete_daily_townhall_tracker(db):
    prepare_data_dtt(db)

    for item in dtt_test_data:
        db.delete_daily_townhall_tracker(item["realm_id"])

        assert len(db.fetch_daily_townhall_tracker(item["realm_id"])) == 0


def test_fetch_last_townhall_ts(db):
    realm_id = 999

    assert -1 == db.fetch_last_townhall_ts_by_realm_id(999)

    generate_townhalls_for_realmid(db, realm_id, given_townhall_values_for_single_realm)

    assert db.fetch_last_townhall_ts_by_realm_id(999) == 3000
