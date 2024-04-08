from __future__ import annotations

import json
from typing import Any

from overlore.errors import ErrorCodes
from overlore.jsonrpc.methods.generate_discussion.entrypoint import Context as GenerateDiscussionContext
from overlore.jsonrpc.methods.generate_discussion.entrypoint import (
    generate_discussion,
)
from overlore.jsonrpc.methods.spawn_npc.entrypoint import Context as SpawnNpcContext
from overlore.jsonrpc.methods.spawn_npc.entrypoint import spawn_npc
from overlore.jsonrpc.types import JsonRpcMethod
from overlore.llm.client import LlmClient
from overlore.llm.guard import AsyncGuard
from overlore.types import (
    Backstory,
    Characteristics,
    DialogueThoughts,
    Discussion,
    NpcAndThoughts,
    NpcEntity,
    NpcIdentity,
    Thought,
)

KATANA_MOCK_TS = 1000


class MockLlmClient(LlmClient):
    def __init__(
        self, embedding_return: list[float], prompt_completion_return: str, thoughts_completion_return: str = ""
    ) -> None:
        self.embedding_return = embedding_return
        self.prompt_completion_return = prompt_completion_return
        self.thoughts_completion_return = thoughts_completion_return
        self.call_number = 0

    async def request_embedding(self, input_str: str, *args: Any, **kwargs: Any) -> list[float]:
        return self.embedding_return

    async def request_prompt_completion(self, prompt: str, instructions: str, *args: Any, **kwargs: Any) -> str:
        ret = ""
        if self.call_number % 2 == 0:
            ret = self.prompt_completion_return
        elif self.thoughts_completion_return:
            ret = self.thoughts_completion_return
        else:
            ret = self.prompt_completion_return
        self.call_number += 1
        return ret


class MockKatanaClient:
    def __init__(self, force_fail: bool = False) -> None:
        self.force_fail = force_fail
        pass

    async def get_contract_nonce(self, contract_address: str) -> int:
        contract_address
        if self.force_fail:
            raise RuntimeError(ErrorCodes.KATANA_UNAVAILABLE)
        return 1

    async def get_katana_ts(self) -> int:
        if self.force_fail:
            raise RuntimeError(ErrorCodes.KATANA_UNAVAILABLE)
        return KATANA_MOCK_TS


class MockToriiClient:
    def __init__(self, npcs_return: list[NpcEntity] | None = None, force_fail: bool = False) -> None:
        self.force_fail = force_fail
        if npcs_return is not None:
            self.npcs = npcs_return
        pass

    async def get_npcs_by_realm_entity_id(self, realm_entity_id: int) -> list[NpcEntity]:
        if self.force_fail:
            raise RuntimeError(ErrorCodes.TORII_UNAVAILABLE)
        return [npc for npc in self.npcs if npc["current_realm_entity_id"] == realm_entity_id]

    async def get_realm_owner_wallet_address(self, realm_entity_id: int) -> str:
        if self.force_fail:
            raise RuntimeError(ErrorCodes.TORII_UNAVAILABLE)
        return "0xDEADBEEF"


class MockBootConfig:
    def __init__(self) -> None:
        self.env = {"HOST_ADDRESS": "localhost", "HOST_PORT": "8766"}
        pass


def generate_discussion_json_rpc_method() -> JsonRpcMethod:
    mock_llm_client = MockLlmClient(
        embedding_return=valid_embedding,
        prompt_completion_return=valid_dialogue,
        thoughts_completion_return=valid_thought.model_dump_json(),
    )
    mock_torii_client = MockToriiClient(
        npcs_return=npcs,
    )

    mock_katana_client = MockKatanaClient()
    discussion_guard = AsyncGuard(output_type=Discussion)
    dialogue_thoughts_guard = AsyncGuard(output_type=DialogueThoughts)

    context = GenerateDiscussionContext(
        discussion_guard=discussion_guard,
        dialogue_thoughts_guard=dialogue_thoughts_guard,
        llm_client=mock_llm_client,  # type: ignore[typeddict-item]
        torii_client=mock_torii_client,  # type: ignore[typeddict-item]
        katana_client=mock_katana_client,  # type: ignore[typeddict-item]
    )

    return JsonRpcMethod(
        context=context,
        method=generate_discussion,
    )


def generate_npc_profile_json_rpc_method() -> JsonRpcMethod:
    mock_llm_client = MockLlmClient(
        embedding_return=valid_embedding, prompt_completion_return=valid_npc_profile.model_dump_json()
    )

    mock_torii_client = MockToriiClient()
    mock_katana_client = MockKatanaClient()
    guard = AsyncGuard(output_type=NpcIdentity)
    context = SpawnNpcContext(
        guard=guard,
        llm_client=mock_llm_client,  # type: ignore[typeddict-item]
        torii_client=mock_torii_client,  # type: ignore[typeddict-item]
        katana_client=mock_katana_client,  # type: ignore[typeddict-item]
        lore_machine_pk=TEST_PRIVATE_KEY,
    )

    return JsonRpcMethod(context=context, method=spawn_npc)


def setup_mock_json_rpc_methods() -> list[JsonRpcMethod]:
    json_rpc_methods: list[JsonRpcMethod] = [
        generate_discussion_json_rpc_method(),
        generate_npc_profile_json_rpc_method(),
    ]

    return json_rpc_methods


dialogue = [
    {"dialogue_segment": "HooHaa", "full_name": "Johny Bravo"},
    {"dialogue_segment": "Blabla", "full_name": "Julien Doré"},
]

valid_dialogue = f"""{{"dialogue": {json.dumps(dialogue, ensure_ascii=False)}, "input_score": 0}}"""

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
            full_name="Julien Doré",
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
        characteristics=Characteristics(age=27, role=3, sex=1),
        entity_id=105,
        current_realm_entity_id=1,
        origin_realm_id=26,
    ),
    NpcEntity(
        character_trait="compassionate",
        full_name="Julien Doré",
        characteristics=Characteristics(age=32, role=3, sex=1),
        entity_id=104,
        current_realm_entity_id=1,
        origin_realm_id=26,
    ),
]

valid_embedding = [0.1] * 1536

valid_npc_profile = NpcIdentity(
    character_trait="Generous",
    full_name="Seraphina Rivertree",
    backstory=Backstory(
        backstory="""Seraphina Rivertree is known for her unwavering generosity, always willing to help those in need without expecting anything in return. She's very pretty and young and she doesn't care about other people LOL. She's just doing her own thang brah. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum""",
        poignancy=0,
    ),
)

TEST_PUBLIC_KEY = "0x141A26313BD3355FE4C4F3DDA7E40DFB77CE54AEA5F62578B4EC5AAD8DD63B1"
TEST_PRIVATE_KEY = "0x38A8B43F18016C22F685A41728046DEC4B3E6829A17A2A83D75F1D840E82ED5"
