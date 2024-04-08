import json

import pytest
from guardrails import Guard

from overlore.errors import ErrorCodes
from overlore.jsonrpc.methods.generate_town_hall.response import TownHallBuilder
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.types import Townhall
from tests.jsonrpc.types import MockKatanaClient, MockLlmClient, MockToriiClient


@pytest.mark.asyncio
async def test_generate_town_hall_without_user_input(init_town_hall_builder):
    town_hall_builder = init_town_hall_builder

    realm_entity_id = 1
    params = {"realm_id": 1, "user_input": "", "realm_entity_id": realm_entity_id, "order_id": 1}
    response = await town_hall_builder.build_from_request_params(params=params)

    assert dialogue == response["dialogue"]


@pytest.mark.asyncio
async def test_generate_town_hall_with_user_input(init_town_hall_builder):
    town_hall_builder = init_town_hall_builder

    realm_entity_id = 1
    params = {"realm_id": 1, "user_input": "Hello World!", "realm_entity_id": realm_entity_id, "order_id": 1}
    response = await town_hall_builder.build_from_request_params(params=params)

    assert dialogue == response["dialogue"]


@pytest.mark.asyncio
async def test_generate_town_hall_no_npcs_in_realm(init_town_hall_builder):
    town_hall_builder = init_town_hall_builder

    realm_entity_id = 2
    params = {"realm_id": 1, "user_input": "Hello World!", "realm_entity_id": realm_entity_id, "order_id": 1}

    with pytest.raises(RuntimeError) as error:
        _ = await town_hall_builder.build_from_request_params(params=params)

    assert error.value.args[0] == ErrorCodes.LACK_OF_NPCS


@pytest.mark.asyncio
async def test_generate_town_hall_katana_unavailable(init_town_hall_builder):
    town_hall_builder = init_town_hall_builder
    town_hall_builder.katana_client = MockKatanaClient(force_fail=True)

    realm_entity_id = 1
    params = {"realm_id": 1, "user_input": "Hello World!", "realm_entity_id": realm_entity_id, "order_id": 1}

    with pytest.raises(RuntimeError) as error:
        _ = await town_hall_builder.build_from_request_params(params=params)

    assert error.value.args[0] == ErrorCodes.KATANA_UNAVAILABLE


@pytest.mark.asyncio
async def test_generate_town_hall_torii_unavailable(init_town_hall_builder):
    town_hall_builder = init_town_hall_builder
    town_hall_builder.torii_client = MockToriiClient(force_fail=True)

    realm_entity_id = 1
    params = {"realm_id": 1, "user_input": "Hello World!", "realm_entity_id": realm_entity_id, "order_id": 1}

    with pytest.raises(RuntimeError) as error:
        _ = await town_hall_builder.build_from_request_params(params=params)

    assert error.value.args[0] == ErrorCodes.TORII_UNAVAILABLE


@pytest.fixture
def init_town_hall_builder():
    npc_db = NpcDatabase.instance().init(":memory:")
    events_db = EventsDatabase.instance().init(":memory:")
    town_hall_db = TownhallDatabase.instance().init(":memory:")

    mock_llm_client = MockLlmClient(
        embedding_return=valid_embedding,
        prompt_completion_return=valid_dialogue,
        thoughts_completion_return=json.dumps(valid_thought, ensure_ascii=False),
    )
    mock_torii_client = MockToriiClient()
    mock_katana_client = MockKatanaClient()
    town_hall_guard = Guard.from_pydantic(output_class=Townhall, num_reasks=0)

    town_hall_builder = TownHallBuilder(
        llm_client=mock_llm_client,
        torii_client=mock_torii_client,
        katana_client=mock_katana_client,
        town_hall_guard=town_hall_guard,
    )

    yield town_hall_builder
    npc_db.close_conn()
    events_db.close_conn()
    town_hall_db.close_conn()


dialogue = [
    {"dialogue_segment": "HooHaa", "full_name": "Johny Bravo"},
    {"dialogue_segment": "Blabla", "full_name": "Julien Doré"},
]

valid_dialogue = f"""{{"dialogue": {json.dumps(dialogue, ensure_ascii=False)}}}"""

valid_thought = {
    "npcs": [
        {"full_name": "Johny Bravo", "thoughts": ["Thoughts about HooHaa", "Second thought about HooHaa"]},
        {"full_name": "Julien Doré", "thoughts": ["Thought about blabla", "Second thought about HooHaa"]},
    ]
}

valid_embedding = [0.0, 0.1, 0.2]
