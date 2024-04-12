import json

import pytest

from overlore.errors import ErrorCodes
from overlore.jsonrpc.methods.generate_discussion.response import Context, DiscussionBuilder, MethodParams
from overlore.llm.guard import AsyncGuard
from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.types import (
    Characteristics,
    DialogueThoughts,
    Discussion,
    NpcAndThoughts,
    NpcEntity,
    Thought,
)
from tests.jsonrpc.types import MockKatanaClient, MockLlmClient, MockToriiClient


@pytest.mark.asyncio
async def test_generate_discussion_without_user_input(context: Context):
    params = MethodParams(realm_id=1, user_input="", realm_entity_id=1, order_id=1)
    discussion_builder = await DiscussionBuilder.create(context=context, params=params)
    response = await discussion_builder.create_response()

    assert dialogue == response["dialogue"]


@pytest.mark.asyncio
async def test_generate_discussion_with_user_input(context: Context):
    params = MethodParams(realm_id=1, user_input="Hello World!", realm_entity_id=1, order_id=1)

    discussion_builder = await DiscussionBuilder.create(context=context, params=params)
    response = await discussion_builder.create_response()

    assert dialogue == response["dialogue"]


@pytest.mark.asyncio
async def test_generate_discussion_no_npcs_in_realm(context: Context):
    params = MethodParams(realm_id=1, user_input="Hello World!", realm_entity_id=2, order_id=1)
    with pytest.raises(RuntimeError) as error:
        _ = await DiscussionBuilder.create(context=context, params=params)

    assert error.value.args[0] == ErrorCodes.LACK_OF_NPCS


@pytest.mark.asyncio
async def test_generate_discussion_katana_unavailable(context: Context):
    realm_entity_id = 1
    params = MethodParams(realm_id=1, user_input="Hello World!", realm_entity_id=realm_entity_id, order_id=1)

    context["katana_client"] = MockKatanaClient(force_fail=True)

    with pytest.raises(RuntimeError) as error:
        _ = await DiscussionBuilder.create(context=context, params=params)

    assert error.value.args[0] == ErrorCodes.KATANA_UNAVAILABLE


@pytest.mark.asyncio
async def test_generate_discussion_torii_unavailable(context: Context):
    realm_entity_id = 1
    params = MethodParams(realm_id=1, user_input="Hello World!", realm_entity_id=realm_entity_id, order_id=1)

    context["torii_client"] = MockToriiClient(force_fail=True)

    with pytest.raises(RuntimeError) as error:
        _ = await DiscussionBuilder.create(context=context, params=params)

    assert error.value.args[0] == ErrorCodes.TORII_UNAVAILABLE


@pytest.fixture
def context():
    npc_db = NpcDatabase.instance().init(":memory:")
    events_db = EventsDatabase.instance().init(":memory:")
    discussion_db = DiscussionDatabase.instance().init(":memory:")

    mock_llm_client = MockLlmClient(
        embedding_return=valid_embedding,
        prompt_completion_return=valid_response,
        thoughts_completion_return=valid_thought.model_dump_json(),
    )
    mock_torii_client = MockToriiClient(
        npcs_return=npcs,
    )

    mock_katana_client = MockKatanaClient()
    discussion_guard = AsyncGuard(output_type=Discussion)
    dialogue_thoughts_guard = AsyncGuard(output_type=DialogueThoughts)

    context = Context(
        discussion_guard=discussion_guard,
        dialogue_thoughts_guard=dialogue_thoughts_guard,
        llm_client=mock_llm_client,
        torii_client=mock_torii_client,
        katana_client=mock_katana_client,
    )

    yield context
    npc_db.close_conn()
    events_db.close_conn()
    discussion_db.close_conn()


dialogue = [
    {"dialogue_segment": "HooHaa", "full_name": "Johny Bravo"},
    {"dialogue_segment": "Blabla", "full_name": "Julien Doré"},
]

valid_response = f"""{{"dialogue": {json.dumps(dialogue, ensure_ascii=False)}, "input_score": 0}}"""

valid_thought = DialogueThoughts(
    npcs=[
        NpcAndThoughts(
            full_name="Johny Bravo",
            thoughts=[
                Thought(thought="Thoughts about HooHaa", poignancy=10),
                Thought(thought="Second thought about HooHaa", poignancy=10),
            ],
        ),
        NpcAndThoughts(
            full_name="Julien Dort",
            thoughts=[
                Thought(thought="Thought about blabla", poignancy=10),
                Thought(thought="Second thought about HooHaa", poignancy=10),
            ],
        ),
    ]
)

npcs = [
    NpcEntity(
        character_trait="Generous",
        full_name="Johny Bravo",
        characteristics=Characteristics(age=27, role=3, sex=1).model_dump(),
        entity_id=105,
        current_realm_entity_id=1,
        origin_realm_id=26,
    ),
    NpcEntity(
        character_trait="compassionate",
        full_name="Julien Dort",
        characteristics=Characteristics(age=32, role=3, sex=1).model_dump(),
        entity_id=104,
        current_realm_entity_id=1,
        origin_realm_id=26,
    ),
]

valid_embedding = [0.0, 0.1, 0.2]
