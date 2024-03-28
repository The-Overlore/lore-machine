import json
import logging
import random
from typing import TypedDict, cast

from guardrails import Guard
from jsonrpcserver import Error, InvalidParams, Result, Success, method
from pydantic import BaseModel
from rich import print

from overlore.config import BootConfig, global_config
from overlore.graphql.client import ToriiClient
from overlore.jsonrpc.methods.spawn_npc.constants import NPC_PROFILE_SYSTEM_STRING, NPC_PROFILE_USER_STRING
from overlore.jsonrpc.methods.spawn_npc.utils import get_contract_nonce
from overlore.llm.client import AsyncOpenAiClient, LlmClient
from overlore.llm.constants import ChatCompletionModel
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.npcs.constants import TRAIT_TYPE
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.types import NpcProfile
from overlore.utils import sign_parameters

logger = logging.getLogger("overlore")


class MethodParams(BaseModel):
    realm_entity_id: int


class SuccessResponse(TypedDict):
    npc: NpcProfile
    signature: list[str]


@method
async def spawn_npc(params: MethodParams) -> Result:
    try:
        MethodParams.model_validate_json(json.dumps(params), strict=True)
    except ValueError as e:
        return InvalidParams(str(e))

    logger.info(f"Creating an NPC for realm_entity_id: {params['realm_entity_id']}")
    try:
        return await handle_regular_flow(params=params)
    except RuntimeError as e:
        err = e.args[0]
        return Error(err.value, err.name)


async def handle_regular_flow(params: MethodParams) -> Success:
    guard = Guard.from_pydantic(output_class=NpcProfile, instructions=NPC_PROFILE_SYSTEM_STRING, num_reasks=1)
    llm_client = AsyncOpenAiClient()
    torii_client = ToriiClient(torii_url=global_config.env["TORII_GRAPHQL"], events_db=EventsDatabase.instance())
    npc_profile_builder = NpcProfileBuilder(
        llm_client=llm_client, torii_client=torii_client, guard=guard, config=global_config
    )
    response = await npc_profile_builder.build_from_request_params(params=params)
    return Success(json.dumps(response))


class NpcProfileBuilder:
    def __init__(self, llm_client: LlmClient, torii_client: ToriiClient, guard: Guard, config: BootConfig):
        self.llm_client = llm_client
        self.torii_client = torii_client
        self.guard = guard
        self.config = config
        self.formater: LlmFormatter = LlmFormatter()

    async def build_from_request_params(self, params: MethodParams) -> SuccessResponse:
        npc_db = NpcDatabase.instance()

        realm_entity_id = params["realm_entity_id"]

        realm_owner_wallet_address = await self.torii_client.get_realm_owner_wallet_address(
            realm_entity_id=realm_entity_id
        )

        npc_profile = npc_db.fetch_npc_profile_by_realm_entity_id(realm_entity_id)

        if npc_profile is None:
            logger.info(f"Generating new npc profile for realm_entity_id {realm_entity_id}")

            prompt_for_llm_call = self.prepare_prompt_for_llm_call()

            npc_profile = await self.request_npc_profile_generation_with_guard(prompt_for_llm_call)

            npc_db.insert_npc_profile(realm_entity_id, npc_profile)

        else:
            logger.info(f"Existing npc profile found for realm_entity_id {realm_entity_id}")

        signature = await self.create_signature_for_response(
            realm_owner_wallet_address=realm_owner_wallet_address, npc_profile=npc_profile
        )

        return SuccessResponse(npc=npc_profile, signature=signature)

    def prepare_prompt_for_llm_call(self) -> str:
        trait_type = TRAIT_TYPE[random.randrange(2)]
        prompt = NPC_PROFILE_USER_STRING.format(trait_type=trait_type)
        return prompt

    async def request_npc_profile_generation_with_guard(self, prompt=str) -> NpcProfile:
        _, validated_response, *_ = await self.guard(
            llm_api=self.llm_client.request_prompt_completion,
            model=ChatCompletionModel.GPT_3_5_TURBO.value,
            temperature=1.8,
            prompt=prompt,
        )
        print(self.guard.history.last.tree)

        return cast(NpcProfile, validated_response)

    async def create_signature_for_response(
        self, realm_owner_wallet_address: str, npc_profile: NpcProfile
    ) -> tuple[NpcProfile, list[str]]:
        nonce = await get_contract_nonce(
            katana_url=self.config.env["KATANA_URL"],
            contract_address=realm_owner_wallet_address,
        )

        signature_params = [
            nonce,
            npc_profile["characteristics"]["age"],  # type: ignore[index]
            npc_profile["characteristics"]["role"],  # type: ignore[index]
            npc_profile["characteristics"]["sex"],  # type: ignore[index]
            npc_profile["character_trait"],  # type: ignore[index]
            npc_profile["full_name"],  # type: ignore[index]
        ]
        signature = sign_parameters(signature_params, self.config.env["LOREMACHINE_PRIVATE_KEY"])

        return [str(signature[0]), str(signature[1])]
