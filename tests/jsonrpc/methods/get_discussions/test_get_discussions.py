import pytest

from overlore.jsonrpc.methods.get_discussions.response import (
    Context,
    DiscussionGetter,
    MethodParams,
    SuccessResponse,
)
from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.types import StorableDiscussion
from overlore.types import Characteristics, DialogueSegment, Discussion, NpcEntity


@pytest.mark.asyncio
async def test_get_valid_response_single_dialogue(context: Context):
    params = MethodParams(start_time=0, end_time=10, realm_id=REALM_ID)
    discussion_getter = DiscussionGetter.create(context=context, params=params)
    response = discussion_getter.create_response()

    assert SuccessResponse(discussions=[DIALOGUE_TS_0], realm_id=REALM_ID) == response


@pytest.mark.asyncio
async def test_get_valid_response_multiple_dialogues(context: Context):
    params = MethodParams(start_time=0, realm_id=REALM_ID)
    discussion_getter = DiscussionGetter.create(context=context, params=params)
    response = discussion_getter.create_response()

    assert SuccessResponse(discussions=[DIALOGUE_TS_0, DIALOGUE_TS_1000], realm_id=REALM_ID) == response


@pytest.mark.asyncio
async def test_get_valid_response_no_dialogues(context: Context):
    params = MethodParams(start_time=TOO_BIG_START_TIME, realm_id=REALM_ID)
    discussion_getter = DiscussionGetter.create(context=context, params=params)
    response = discussion_getter.create_response()

    assert SuccessResponse(discussions=[], realm_id=REALM_ID) == response


@pytest.fixture
def context():
    discussion_db = DiscussionDatabase.instance().init(":memory:")

    discussion_db.insert_discussion(DIALOGUE_TS_0)
    discussion_db.insert_discussion(DIALOGUE_TS_1000)
    discussion_db.insert_discussion(DIALOGUE_REALM_ID_DIFFERENT)

    context = Context()

    yield context
    discussion_db.close_conn()


# TEST DATA
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
REALM_ID = 1

SENTENCE_JOHN = "Hello World!"
SENTENCE_FRED = "Indeed! Hello World!"
USER_INPUT = "Hello Eternum World!"

DIALOGUE_JOHN = DialogueSegment(dialogue_segment=SENTENCE_JOHN, full_name="John")
DIALOGUE_FRED = DialogueSegment(dialogue_segment=SENTENCE_FRED, full_name="Fred")


DIALOGUE_TS_0 = StorableDiscussion.from_llm_output(
    realm_id=REALM_ID,
    ts=0,
    discussion=Discussion(dialogue=[DIALOGUE_JOHN, DIALOGUE_FRED], input_score=10),
    user_input=USER_INPUT,
    realm_npcs=REALM_NPCS,
)
DIALOGUE_TS_1000 = StorableDiscussion.from_llm_output(
    realm_id=REALM_ID,
    ts=1000,
    discussion=Discussion(dialogue=[DIALOGUE_JOHN, DIALOGUE_FRED], input_score=10),
    user_input=USER_INPUT,
    realm_npcs=REALM_NPCS,
)
DIALOGUE_REALM_ID_DIFFERENT = StorableDiscussion.from_llm_output(
    realm_id=REALM_ID + 1,
    ts=0,
    discussion=Discussion(dialogue=[DIALOGUE_JOHN, DIALOGUE_FRED], input_score=10),
    user_input=USER_INPUT,
    realm_npcs=REALM_NPCS,
)

TOO_BIG_START_TIME = 9999
