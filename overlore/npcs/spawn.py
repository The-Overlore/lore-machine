import logging

from starknet_py.hash.utils import ECSignature

from overlore.config import BootConfig
from overlore.eternum.types import Npc
from overlore.graphql.query import Queries, run_torii_query
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.npc_db import NpcDatabase
from overlore.types import NpcSpawnMsgData
from overlore.utils import get_contract_nonce, sign_parameters

logger = logging.getLogger("overlore")


async def build_response(realm_entity_id: int, npc: Npc, config: BootConfig) -> tuple[Npc, ECSignature]:
    data = run_torii_query(config.env["TORII_GRAPHQL"], Queries.OWNER.value.format(entity_id=realm_entity_id))
    realm_owner_address = data["ownerModels"]["edges"][0]["node"]["address"]

    nonce = await get_contract_nonce(
        katana_url=config.env["KATANA_URL"],
        contract_address=realm_owner_address,
    )

    # do I have to increment the nonce by one?
    signature_params = [
        nonce,
        npc["characteristics"]["age"],
        npc["characteristics"]["role"],
        npc["characteristics"]["sex"],
        npc["character_trait"],
        npc["full_name"],
    ]
    signature = sign_parameters(signature_params, config.env["LOREMACHINE_PRIVATE_KEY"])

    return (npc, signature)


async def spawn_npc(data: NpcSpawnMsgData, config: BootConfig) -> tuple[Npc, ECSignature]:
    llm_formatter = LlmFormatter()
    npc_db = NpcDatabase.instance()
    open_ai = OpenAIHandler.instance()

    realm_entity_id = data["realm_entity_id"]
    npc = npc_db.fetch_npc_spawn_by_realm(realm_entity_id)

    if npc is None:
        logger.info(f"Generating new npc profile for realm_entity_id {realm_entity_id}")
        npc_string = await open_ai.generate_npc_profile()

        npc = llm_formatter.convert_llm_response_to_profile(npc_string)

        npc["full_name"] = (await open_ai.generate_npc_name(npc["characteristics"]["sex"])).strip()

        npc_db.insert_npc_spawn(realm_entity_id, npc)
    else:
        logger.info(f"Existing npc profile found for realm_entity_id {realm_entity_id}")

    return await build_response(realm_entity_id=realm_entity_id, npc=npc, config=config)
