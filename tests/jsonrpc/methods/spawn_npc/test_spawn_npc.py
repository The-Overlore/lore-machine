import json

import pytest
from guardrails import Guard
from starknet_py.cairo.felt import encode_shortstring
from starknet_py.hash.utils import compute_hash_on_elements, verify_message_signature

from overlore.errors import ErrorCodes
from overlore.jsonrpc.methods.spawn_npc.response import NpcProfileBuilder
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.types import NpcProfile
from tests.jsonrpc.types import MockKatanaClient, MockLlmClient, MockToriiClient


@pytest.mark.asyncio
async def test_spawn_npc_successful(init_npc_profile_builder):
    npc_profile_builder = init_npc_profile_builder

    realm_entity_id = 1
    params = {"realm_id": 1, "user_input": "", "realm_entity_id": realm_entity_id, "order_id": 1}
    response = await npc_profile_builder.build_from_request_params(params=params)

    assert response["npc"] == valid_npc_profile


@pytest.mark.asyncio
async def test_spawn_npc_valid_signature(init_npc_profile_builder):
    npc_profile_builder = init_npc_profile_builder

    realm_entity_id = 1
    params = {"realm_id": 1, "user_input": "", "realm_entity_id": realm_entity_id, "order_id": 1}
    response = await npc_profile_builder.build_from_request_params(params=params)

    npc = response["npc"]
    nonce = await npc_profile_builder.katana_client.get_contract_nonce(1)

    msg = [
        nonce,
        npc["characteristics"]["age"],
        npc["characteristics"]["role"],
        npc["characteristics"]["sex"],
        encode_shortstring(npc["character_trait"]),
        encode_shortstring(npc["full_name"]),
    ]
    signature = [int(elem) for elem in response["signature"]]
    msg_hash = compute_hash_on_elements(msg)
    assert verify_message_signature(msg_hash=msg_hash, signature=signature, public_key=int(TEST_PUBLIC_KEY, base=16))


@pytest.mark.asyncio
async def test_spawn_npc_katana_unavailable(init_npc_profile_builder):
    npc_profile_builder = init_npc_profile_builder
    npc_profile_builder.katana_client = MockKatanaClient(force_fail=True)

    realm_entity_id = 1
    params = {"realm_id": 1, "user_input": "", "realm_entity_id": realm_entity_id, "order_id": 1}

    with pytest.raises(RuntimeError) as error:
        _ = await npc_profile_builder.build_from_request_params(params=params)

    assert error.value.args[0] == ErrorCodes.KATANA_UNAVAILABLE


@pytest.mark.asyncio
async def test_spawn_npc_torii_unavailable(init_npc_profile_builder):
    npc_profile_builder = init_npc_profile_builder
    npc_profile_builder.torii_client = MockToriiClient(force_fail=True)

    realm_entity_id = 1
    params = {"realm_id": 1, "user_input": "", "realm_entity_id": realm_entity_id, "order_id": 1}

    with pytest.raises(RuntimeError) as error:
        _ = await npc_profile_builder.build_from_request_params(params=params)

    assert error.value.args[0] == ErrorCodes.TORII_UNAVAILABLE


@pytest.fixture
def init_npc_profile_builder():
    npc_db = NpcDatabase.instance().init(":memory:")
    events_db = EventsDatabase.instance().init(":memory:")
    townhall_db = TownhallDatabase.instance().init(":memory:")

    mock_llm_client = MockLlmClient(
        embedding_return=valid_embedding, promp_completion_return=json.dumps(valid_npc_profile)
    )
    mock_torii_client = MockToriiClient()
    mock_katana_client = MockKatanaClient()
    guard = Guard.from_pydantic(output_class=NpcProfile, num_reasks=0)

    npc_profile_builder = NpcProfileBuilder(
        llm_client=mock_llm_client,
        torii_client=mock_torii_client,
        katana_client=mock_katana_client,
        lore_machine_pk=TEST_PRIVATE_KEY,
        guard=guard,
    )

    yield npc_profile_builder
    npc_db.close_conn()
    events_db.close_conn()
    townhall_db.close_conn()


TEST_PUBLIC_KEY = "0x141A26313BD3355FE4C4F3DDA7E40DFB77CE54AEA5F62578B4EC5AAD8DD63B1"
TEST_PRIVATE_KEY = "0x38A8B43F18016C22F685A41728046DEC4B3E6829A17A2A83D75F1D840E82ED5"

valid_embedding = [0.0, 0.1, 0.2]
valid_npc_profile = {
    "character_trait": "Generous",
    "full_name": "Seraphina Rivertree",
    "description": (
        "Seraphina Rivertree is known for her unwavering generosity, always willing to help those in need without"
        " expecting anything in return."
    ),
    "characteristics": {"age": 27, "role": 3, "sex": 1},
}
