from __future__ import annotations

from typing import Any

from overlore.errors import ErrorCodes
from overlore.llm.client import LlmClient
from overlore.types import NpcEntity


class MockLlmClient(LlmClient):
    def __init__(
        self, embedding_return: list[float], prompt_completion_return: str, thoughts_completion_return: str = ""
    ) -> MockLlmClient:
        self.embedding_return = embedding_return
        self.prompt_completion_return = prompt_completion_return
        self.thoughts_completion_return = thoughts_completion_return
        self.call_number = 0

    async def request_embedding(self, input_str: str, *args, **kwargs) -> list[float]:
        return self.embedding_return

    async def request_prompt_completion(self, prompt: str, instructions: str, *args: Any, **kwargs: Any) -> str:
        if self.call_number == 0:
            self.call_number += 1
            return self.prompt_completion_return
        else:
            return self.thoughts_completion_return


class MockKatanaClient:
    def __init__(self, force_fail: bool = False) -> MockKatanaClient:
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
        return 1000


class MockToriiClient:
    def __init__(self, npcs_return: list[NpcEntity] = None, force_fail: bool = False) -> MockToriiClient:
        self.force_fail = force_fail
        self.npcs = npcs_return
        pass

    async def get_npcs_by_realm_entity_id(self, realm_entity_id: int) -> list[NpcEntity]:
        if self.force_fail:
            raise RuntimeError(ErrorCodes.TORII_UNAVAILABLE)
        return [npc for npc in self.npcs if npc["current_realm_entity_id"] == realm_entity_id]

    async def get_realm_owner_wallet_address(self, realm_entity_id: int):
        if self.force_fail:
            raise RuntimeError(ErrorCodes.TORII_UNAVAILABLE)
        return "0xDEADBEEF"


class MockBootConfig:
    def __init__(self) -> None:
        self.env = {"HOST_ADDRESS": "localhost", "HOST_PORT": "8766"}
        pass
