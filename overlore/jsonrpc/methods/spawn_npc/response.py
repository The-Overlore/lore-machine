import logging
import random
from typing import TypedDict

from openai import BaseModel

from overlore.constants import ROLES, SEX, TRAIT_TYPE
from overlore.jsonrpc.methods.spawn_npc.constants import NPC_PROFILE_SYSTEM_STRING, NPC_PROFILE_USER_STRING
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.llm.constants import ChatCompletionModel
from overlore.llm.guard import AsyncGuard
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.sqlite.npc_db import NpcDatabase
from overlore.torii.client import ToriiClient
from overlore.types import Characteristics, NpcIdentity, NpcProfile
from overlore.utils import sign_parameters

logger = logging.getLogger("overlore")


class RandGenerator:
    def generate_age(self) -> int:
        return random.randint(15, 65)

    def generate_sex(self) -> int:
        return random.randint(0, 1)

    def generate_role(self) -> int:
        return random.randint(0, len(ROLES) - 1)


class Context(TypedDict):
    guard: AsyncGuard
    llm_client: AsyncOpenAiClient
    torii_client: ToriiClient
    katana_client: KatanaClient
    lore_machine_pk: str


class MethodParams(BaseModel):
    realm_entity_id: int


class SuccessResponse(TypedDict):
    npc: NpcProfile
    signature: list[str]


class NpcProfileBuilder:
    def __init__(self, context: Context, params: MethodParams, rand_generator: RandGenerator):
        self.formater: LlmFormatter = LlmFormatter()
        self.context: Context = context
        self.params: MethodParams = params
        self.rand_generator: RandGenerator = rand_generator

    async def create_response(
        self,
    ) -> SuccessResponse:
        npc_db = NpcDatabase.instance()

        realm_entity_id = self.params.realm_entity_id

        realm_owner_wallet_address = await self.context["torii_client"].get_realm_owner_wallet_address(
            realm_entity_id=realm_entity_id
        )

        npc_profile = npc_db.fetch_npc_profile_by_realm_entity_id(realm_entity_id)

        if npc_profile is None:
            logger.info(f"Generating new npc profile for realm_entity_id {realm_entity_id}")

            age = self.rand_generator.generate_age()
            role = self.rand_generator.generate_role()
            sex = self.rand_generator.generate_sex()

            prompt_for_llm_call = self.prepare_prompt_for_llm_call(age, ROLES[role], SEX[sex])

            npc_background = await self.request_npc_profile_generation_with_guard(prompt_for_llm_call)

            npc_profile = NpcProfile(
                full_name=npc_background.full_name,
                character_trait=npc_background.character_trait,
                backstory=npc_background.backstory,
                characteristics=Characteristics(age=age, role=role, sex=sex),
            )

            npc_db.insert_npc_profile(realm_entity_id, npc_profile)

        else:
            logger.info(f"Existing npc profile found for realm_entity_id {realm_entity_id}")

        signature = await self.create_signature_for_response(
            realm_owner_wallet_address=realm_owner_wallet_address, npc_profile=npc_profile
        )

        return SuccessResponse(npc=npc_profile, signature=signature)
        # return SuccessResponse(npc=cast(NpcProfile, npc_profile.model_dump()), signature=signature)

    def prepare_prompt_for_llm_call(self, age: int, role: str, sex: str) -> str:
        trait_type = TRAIT_TYPE[random.randrange(2)]
        prompt = NPC_PROFILE_USER_STRING.format(trait_type=trait_type, age=age, role=role, sex=sex)
        return prompt

    async def request_npc_profile_generation_with_guard(self, prompt: str) -> NpcIdentity:
        response = await self.context["guard"].call_llm_with_guard(
            api_function=self.context["llm_client"].request_prompt_completion,
            instructions=NPC_PROFILE_SYSTEM_STRING,
            prompt=prompt,
            model=ChatCompletionModel.GPT_3_5_TURBO.value,
            temperature=1.6,
        )

        return response  # type: ignore[no-any-return]

    async def create_signature_for_response(
        self, realm_owner_wallet_address: str, npc_profile: NpcProfile
    ) -> list[str]:
        nonce = await self.context["katana_client"].get_contract_nonce(
            contract_address=realm_owner_wallet_address,
        )

        signature_params = [
            nonce,
            npc_profile["characteristics"]["age"],
            npc_profile["characteristics"]["role"],
            npc_profile["characteristics"]["sex"],
            npc_profile["character_trait"],
            npc_profile["full_name"],
        ]
        signature = sign_parameters(signature_params, self.context["lore_machine_pk"])

        return [str(signature[0]), str(signature[1])]
