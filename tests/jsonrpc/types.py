from __future__ import annotations

from overlore.errors import ErrorCodes
from overlore.llm.client import LlmClient
from overlore.types import NpcEntity


class MockLlmClient(LlmClient):
    def __init__(self, embedding_return: list[float], promp_completion_return: str) -> MockLlmClient:
        self.embedding_return = embedding_return
        self.promp_completion_return = promp_completion_return
        pass

    async def request_embedding(self, input_str: str, *args, **kwargs) -> list[float]:
        return self.embedding_return

    async def request_prompt_completion(self, *args, **kwargs) -> str:
        return self.promp_completion_return


class MockKatanaClient:
    def __init__(self, force_fail: bool = False) -> MockKatanaClient:
        self.force_fail = force_fail
        pass

    async def get_contract_nonce(self, contract_address: str) -> int:
        contract_address
        if self.force_fail:
            raise RuntimeError(ErrorCodes.KATANA_UNAVAILABLE)
        return 1

    async def get_katana_timestamp(self) -> int:
        if self.force_fail:
            raise RuntimeError(ErrorCodes.KATANA_UNAVAILABLE)
        return 1000


class MockToriiClient:
    def __init__(self, force_fail: bool = False) -> MockToriiClient:
        self.force_fail = force_fail
        pass

    async def get_npcs_by_realm_entity_id(self, realm_entity_id: int) -> list[NpcEntity]:
        if self.force_fail:
            raise RuntimeError(ErrorCodes.TORII_UNAVAILABLE)
        npcs = [
            {
                "character_trait": "Generous",
                "full_name": "Johny Bravo",
                "characteristics": {"age": 27, "role": 3, "sex": 1},
                "entity_id": 105,
                "current_realm_entity_id": 1,
                "origin_realm_id": 26,
            },
            {
                "character_trait": "compassionate",
                "full_name": "Julien Doré",
                "characteristics": {"age": 32, "role": 3, "sex": 1},
                "entity_id": 104,
                "current_realm_entity_id": 1,
                "origin_realm_id": 26,
            },
        ]
        return [npc for npc in npcs if npc["current_realm_entity_id"] == realm_entity_id]

    async def get_realm_owner_wallet_address(self, realm_entity_id: int):
        if self.force_fail:
            raise RuntimeError(ErrorCodes.TORII_UNAVAILABLE)
        return "0xDEADBEEF"
