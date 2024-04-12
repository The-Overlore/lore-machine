import pytest

from overlore.errors import ErrorCodes
from overlore.sqlite.townhall_db import TownhallDatabase
from tests.utils.townhall_db_test_utils import (
    ThoughtsDatabaseFiller,
    daily_town_hall_tracker_data,
    format_townhalls,
    generate_townhalls_for_realmid,
    given_thoughts,
    given_townhall_values,
    given_townhall_values_for_single_realm,
    prepare_daily_town_hall_tracker_data,
)


@pytest.fixture
def db():
    db = TownhallDatabase.instance().init(":memory:")
    yield db
    db.close_conn()


def test_insert_and_fetch_townhall_discussion(db: TownhallDatabase):
    for item in given_townhall_values:
        added_row_id = db.insert_townhall_discussion(
            item["realm_id"], item["discussion"], item["input"], item["input_score"], item["ts"]
        )
        retrieved_entry = db.fetch_townhalls_by_realm_id(item["realm_id"])[0]

        assert added_row_id == item["rowid"], f"Expected rowid {item['rowid']}, got {added_row_id}"
        assert retrieved_entry == (
            item["discussion"],
            item["input"],
        ), f"Expected profile '{(item['discussion'], item['input'])}', got '{retrieved_entry}'"


def test_fetch_multiple_townhalls(db: TownhallDatabase):
    realm_id = 999
    generate_townhalls_for_realmid(db, realm_id, given_townhall_values_for_single_realm)

    retrieved_entries = db.fetch_townhalls_by_realm_id(realm_id)

    assert retrieved_entries == format_townhalls(given_townhall_values_for_single_realm)


def test_insert_and_fetch_npc_thought(db: TownhallDatabase):
    for item in given_thoughts:
        added_row_id = db.insert_npc_thought(
            item["npc_entity_id"], item["thought"], item["poignancy"], item["ts"], item["embedding"]
        )
        retrieved_entry = db.fetch_npc_thought_by_row_id(added_row_id)

        assert added_row_id == item["rowid"], f"Expected rowid {item['rowid']}, got {added_row_id}"
        assert retrieved_entry == item["thought"], f"Expected thought '{item['thought']}', got '{retrieved_entry}'"


def test_insert_and_fetch_daily_townhall_tracker(db: TownhallDatabase):
    for item in daily_town_hall_tracker_data:
        added_row_id = db.insert_or_update_daily_townhall_tracker(item["realm_id"], item["event_row_id"])

        assert item["row_id"] == added_row_id
        assert [item["event_row_id"]] == db.fetch_daily_townhall_tracker(item["realm_id"])


def test_update_daily_townhall_tracker(db: TownhallDatabase):
    row_ids = []
    for item in daily_town_hall_tracker_data:
        updated_count = db.insert_or_update_daily_townhall_tracker(1, item["event_row_id"])
        row_ids.append(item["event_row_id"])

        assert updated_count == 1
        assert row_ids == db.fetch_daily_townhall_tracker(1)


def delete_daily_townhall_tracker(db: TownhallDatabase):
    prepare_daily_town_hall_tracker_data(db)

    for item in daily_town_hall_tracker_data:
        db.delete_daily_townhall_tracker(item["realm_id"])

        assert len(db.fetch_daily_townhall_tracker(item["realm_id"])) == 0


def test_fetch_last_townhall_ts(db: TownhallDatabase):
    realm_id = 999

    assert -1 == db.fetch_last_townhall_ts_by_realm_id(realm_id)

    generate_townhalls_for_realmid(db, realm_id, given_townhall_values_for_single_realm)

    assert db.fetch_last_townhall_ts_by_realm_id(realm_id) == 3000


def test_insert_empty_thought_embedding(db: TownhallDatabase):
    npc_entity_id = 1
    embedding = []
    thought = "thought"
    with pytest.raises(RuntimeError) as error:
        _ = db.insert_npc_thought(
            npc_entity_id=npc_entity_id, thought=thought, poignancy=1, katana_ts=1, thought_embedding=embedding
        )

    assert error.value.args[0] == ErrorCodes.INSERTING_EMPTY_EMBEDDING


def test_get_highest_scoring_thought_with_time_increase(db: TownhallDatabase):
    iterations = 100
    thoughts_filler = ThoughtsDatabaseFiller(database=db)

    last_inserted_id = thoughts_filler.populate_with_time_increase(iterations)

    most_recent_thought = db.fetch_npc_thought_by_row_id(last_inserted_id)

    (highest_scoring_though, _, _, _) = db.get_highest_scoring_thought(
        query_embedding=[1.0] * 1536, npc_entity_id=1, katana_ts=iterations
    )

    assert most_recent_thought == highest_scoring_though

    not_so_recent_thought = db.fetch_npc_thought_by_row_id(1)

    assert not_so_recent_thought != highest_scoring_though


def test_get_highest_scoring_thought_with_cosine_increase(db: TownhallDatabase):
    iterations = 100
    thoughts_filler = ThoughtsDatabaseFiller(database=db)

    last_inserted_id = thoughts_filler.populate_with_cosine_increase(iterations)

    most_relevant_thought = db.fetch_npc_thought_by_row_id(last_inserted_id)

    query_embedding = [float(last_inserted_id)] + ([float(100)] * 1535)

    (highest_scoring_though, _, _, _) = db.get_highest_scoring_thought(
        query_embedding=query_embedding, npc_entity_id=1, katana_ts=1
    )

    assert most_relevant_thought == highest_scoring_though

    least_relevant_thought = db.fetch_npc_thought_by_row_id(1)

    assert least_relevant_thought != highest_scoring_though


def test_get_higest_scoring_thought_with_poignancy_increase(db: TownhallDatabase):
    iterations = 10
    thoughts_filler = ThoughtsDatabaseFiller(database=db)

    last_inserted_id = thoughts_filler.populate_with_cosine_increase(iterations)

    most_similar_thought = db.fetch_npc_thought_by_row_id(last_inserted_id)

    (highest_scoring_though, _, _, _) = db.get_highest_scoring_thought(
        query_embedding=[1.0] * 1536, npc_entity_id=1, katana_ts=1
    )

    assert most_similar_thought == highest_scoring_though

    least = db.fetch_npc_thought_by_row_id(1)

    assert least != highest_scoring_though
