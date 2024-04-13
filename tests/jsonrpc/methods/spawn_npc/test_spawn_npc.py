import json
import threading

import pytest
from starknet_py.cairo.felt import encode_shortstring
from starknet_py.hash.utils import compute_hash_on_elements, verify_message_signature

from overlore.errors import ErrorCodes
from overlore.jsonrpc.methods.spawn_npc.response import MethodParams, NpcProfileBuilder
from overlore.jsonrpc.methods.spawn_npc.spawn_npc import Context, spawn_npc
from overlore.jsonrpc.setup import launch_json_rpc_server
from overlore.jsonrpc.types import JsonRpcMethod
from overlore.llm.guard import AsyncGuard
from overlore.mocks import MockBootConfig, MockKatanaClient, MockLlmClient, MockToriiClient
from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.types import Backstory, Characteristics, NpcProfile
from tests.jsonrpc.utils import call_json_rpc_server, run_async_function


@pytest.mark.asyncio
async def test_spawn_npc_successful(context: Context):
    realm_entity_id = 1
    params = MethodParams(realm_entity_id=realm_entity_id)
    npc_profile_builder = NpcProfileBuilder(context=context, params=params)
    response = await npc_profile_builder.create_response()

    assert response["npc"] == valid_npc_profile.model_dump()


@pytest.mark.asyncio
async def test_spawn_npc_valid_signature(context: Context):
    realm_entity_id = 1
    params = MethodParams(realm_entity_id=realm_entity_id)
    npc_profile_builder = NpcProfileBuilder(context=context, params=params)

    response = await npc_profile_builder.create_response()

    npc = response["npc"]
    nonce = await npc_profile_builder.context["katana_client"].get_contract_nonce(1)

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
async def test_spawn_npc_load(init_load_tester_config):
    [boot_config, json_rpc_method] = init_load_tester_config

    launch_json_rpc_server(config=boot_config, methods=[json_rpc_method])

    NUM_THREADS = 100

    threads = []
    results = []
    url = f"http://{boot_config.env['HOST_ADDRESS']}:{boot_config.env['HOST_PORT']}"
    for _i in range(NUM_THREADS):
        thread = threading.Thread(
            target=run_async_function,
            args=(
                call_json_rpc_server,
                url,
                "spawn_npc",
                {"realm_entity_id": 1},
                results,
            ),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    for result in results:
        npc_profile = json.loads(result["result"])["npc"]
        assert npc_profile == valid_npc_profile.model_dump()


@pytest.mark.asyncio
async def test_spawn_npc_katana_unavailable(context: Context):
    context["katana_client"] = MockKatanaClient(force_fail=True)

    realm_entity_id = 1
    params = MethodParams(realm_entity_id=realm_entity_id)
    npc_profile_builder = NpcProfileBuilder(context=context, params=params)

    with pytest.raises(RuntimeError) as error:
        _ = await npc_profile_builder.create_response()

    assert error.value.args[0] == ErrorCodes.KATANA_UNAVAILABLE


@pytest.mark.asyncio
async def test_spawn_npc_torii_unavailable(context: Context):
    realm_entity_id = 1
    params = MethodParams(realm_entity_id=realm_entity_id)
    context["torii_client"] = MockToriiClient(force_fail=True)
    npc_profile_builder = NpcProfileBuilder(context=context, params=params)

    with pytest.raises(RuntimeError) as error:
        _ = await npc_profile_builder.create_response()

    assert error.value.args[0] == ErrorCodes.TORII_UNAVAILABLE


@pytest.fixture
def context():
    npc_db = NpcDatabase.instance().init(":memory:")
    events_db = EventsDatabase.instance().init(":memory:")
    discussion_db = DiscussionDatabase.instance().init(":memory:")

    mock_llm_client = MockLlmClient(
        embedding_return=valid_embedding, prompt_completion_return=valid_npc_profile.model_dump_json()
    )

    mock_torii_client = MockToriiClient()
    mock_katana_client = MockKatanaClient()
    guard = AsyncGuard(output_type=NpcProfile)
    context = Context(
        guard=guard,
        llm_client=mock_llm_client,
        torii_client=mock_torii_client,
        katana_client=mock_katana_client,
        lore_machine_pk=TEST_PRIVATE_KEY,
    )

    yield context

    npc_db.close_conn()
    events_db.close_conn()
    discussion_db.close_conn()


@pytest.fixture
def init_load_tester_config():
    npc_db = NpcDatabase.instance().init(":memory:")
    events_db = EventsDatabase.instance().init(":memory:")
    discussion_db = DiscussionDatabase.instance().init(":memory:")

    mock_llm_client = MockLlmClient(
        embedding_return=valid_embedding, prompt_completion_return=valid_npc_profile.model_dump_json()
    )
    mock_torii_client = MockToriiClient()
    mock_katana_client = MockKatanaClient()
    guard = AsyncGuard(output_type=NpcProfile)

    config = MockBootConfig()

    json_rpc_method = JsonRpcMethod(
        method=spawn_npc,
        context=Context(
            guard=guard,
            llm_client=mock_llm_client,
            torii_client=mock_torii_client,
            katana_client=mock_katana_client,
            lore_machine_pk=TEST_PRIVATE_KEY,
        ),
    )

    yield [config, json_rpc_method]

    npc_db.close_conn()
    events_db.close_conn()
    discussion_db.close_conn()


TEST_PUBLIC_KEY = "0x141A26313BD3355FE4C4F3DDA7E40DFB77CE54AEA5F62578B4EC5AAD8DD63B1"
TEST_PRIVATE_KEY = "0x38A8B43F18016C22F685A41728046DEC4B3E6829A17A2A83D75F1D840E82ED5"

valid_embedding = [0.0, 0.1, 0.2]
valid_npc_profile = NpcProfile(
    character_trait="Generous",
    full_name="Seraphina Rivertree",
    backstory=Backstory(
        backstory="""Seraphina Rivertree is known for her unwavering generosity, always willing to help those in need without expecting anything in return. She's very pretty and young and she doesn't care about other people LOL. She's just doing her own thang brah. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum""",
        poignancy=0,
    ),
    characteristics=Characteristics(age=27, role=3, sex=1),
)
