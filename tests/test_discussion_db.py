import pytest

from overlore.errors import ErrorCodes
from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.types import StorableDiscussion
from overlore.types import Characteristics, DialogueSegment, Discussion, NpcEntity
from tests.utils.discussion_db_test_utils import (
    ThoughtsDatabaseFiller,
    daily_discussion_tracker_data,
    given_thoughts,
    prepare_daily_discussion_tracker_data,
)


@pytest.fixture
def db():
    db = DiscussionDatabase.instance().init(":memory:")
    yield db
    db.close_conn()


def test_insert_and_fetch_discussion(db: DiscussionDatabase):
    for i in range(1, 10):
        storable = StorableDiscussion.from_llm_output(
            discussion=Discussion(
                dialogue=[DialogueSegment(full_name="Fred", dialogue_segment=f"Discussion {i}")], input_score=10
            ),
            ts=i,
            user_input=f"Input: {i}",
            realm_id=i,
            realm_npcs=REALM_NPCS,
        )
        _ = db.insert_discussion(discussion=storable)
        retrieved_discussion = db.fetch_discussions_by_realm_id(realm_id=i)[0]

        assert retrieved_discussion == storable


def test_fetch_multiple_discussions(db: DiscussionDatabase):
    realm_id = 999
    storables = []
    for i in range(1, 10):
        storable = StorableDiscussion.from_llm_output(
            discussion=Discussion(
                dialogue=[DialogueSegment(full_name="Fred", dialogue_segment=f"Discussion {i}")], input_score=10
            ),
            ts=i,
            user_input=f"Input: {i}",
            realm_id=realm_id,
            realm_npcs=REALM_NPCS,
        )
        _ = db.insert_discussion(discussion=storable)
        storables.append(storable)

    assert storables == db.fetch_discussions_by_realm_id(realm_id)


def test_insert_and_fetch_npc_thought(db: DiscussionDatabase):
    for item in given_thoughts:
        added_row_id = db.insert_npc_thought(
            item["npc_entity_id"], item["thought"], item["poignancy"], item["ts"], item["embedding"]
        )
        retrieved_entry = db.fetch_npc_thought_by_row_id(added_row_id)

        assert added_row_id == item["rowid"], f"Expected rowid {item['rowid']}, got {added_row_id}"
        assert retrieved_entry == item["thought"], f"Expected thought '{item['thought']}', got '{retrieved_entry}'"


def test_insert_and_fetch_daily_discussion_tracker(db: DiscussionDatabase):
    for i in range(1, 101):
        added_row_id = db.insert_or_update_events_to_ignore_today(katana_ts=i, realm_id=i, event_id=i)

        assert i == added_row_id
        assert [i] == db.fetch_events_to_ignore_today(realm_id=i)


def test_update_daily_discussion_tracker(db: DiscussionDatabase):
    row_ids = []
    realm_id = 1
    for i in range(1, 101):
        new_row_id = db.insert_or_update_events_to_ignore_today(realm_id=realm_id, katana_ts=i, event_id=i)
        row_ids.append(i)

        assert new_row_id == 1
        assert row_ids == db.fetch_events_to_ignore_today(realm_id)


def delete_events_to_ignore_today(db: DiscussionDatabase):
    prepare_daily_discussion_tracker_data(db)

    for item in daily_discussion_tracker_data:
        db.delete_events_to_ignore_today(item["realm_id"])

        assert len(db.fetch_events_to_ignore_today(item["realm_id"])) == 0


def test_fetch_last_discussion_ts(db: DiscussionDatabase):
    realm_id = 999
    MAX_DISCUSSIONS = 10

    assert -1 == db.fetch_last_discussion_ts_by_realm_id(realm_id)

    for i in range(1, MAX_DISCUSSIONS + 1):
        storable = StorableDiscussion.from_llm_output(
            discussion=Discussion(
                dialogue=[DialogueSegment(full_name="Fred", dialogue_segment=f"Discussion {i}")], input_score=10
            ),
            ts=i,
            user_input=f"Input: {i}",
            realm_id=realm_id,
            realm_npcs=REALM_NPCS,
        )
        _ = db.insert_discussion(discussion=storable)

    assert db.fetch_last_discussion_ts_by_realm_id(realm_id) == MAX_DISCUSSIONS


def test_insert_empty_thought_embedding(db: DiscussionDatabase):
    npc_entity_id = 1
    embedding = []
    thought = "thought"
    with pytest.raises(RuntimeError) as error:
        _ = db.insert_npc_thought(
            npc_entity_id=npc_entity_id, thought=thought, poignancy=1, katana_ts=1, thought_embedding=embedding
        )

    assert error.value.args[0] == ErrorCodes.INSERTING_EMPTY_EMBEDDING


def test_get_highest_scoring_thought_with_time_increase(db: DiscussionDatabase):
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


def test_get_highest_scoring_thought_with_cosine_increase(db: DiscussionDatabase):
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


def test_get_higest_scoring_thought_with_poignancy_increase(db: DiscussionDatabase):
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


JOHN_ENTITY_ID = 1
FRED_ENTITY_ID = 2


JOHN = NpcEntity(
    character_trait="dumb",
    characteristics=Characteristics(age=1, role=1, sex=1),
    current_realm_entity_id=1,
    entity_id=JOHN_ENTITY_ID,
    full_name="John",
    origin_realm_id=1,
)

FRED = NpcEntity(
    character_trait="dumber",
    characteristics=Characteristics(age=1, role=1, sex=1),
    current_realm_entity_id=1,
    entity_id=FRED_ENTITY_ID,
    full_name="Fred",
    origin_realm_id=1,
)

REALM_NPCS = [FRED, JOHN]
