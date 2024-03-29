import logging

from overlore.config import BootConfig
from overlore.graphql.query import Queries, run_torii_query
from overlore.llm.llm import Llm
from overlore.sqlite.npc_db import NpcDatabase
from overlore.types import NpcProfile, NpcSpawnMsgData
from overlore.utils import get_contract_nonce, sign_parameters

logger = logging.getLogger("overlore")


def build_response(realm_entity_id: int, npc: NpcProfile, config: BootConfig) -> tuple[NpcProfile, list[str]]:
    data = run_torii_query(config.env["TORII_GRAPHQL"], Queries.OWNER.value.format(entity_id=realm_entity_id))
    realm_owner_address = data["ownerModels"]["edges"][0]["node"]["address"]

    nonce = get_contract_nonce(
        katana_url=config.env["KATANA_URL"],
        contract_address=realm_owner_address,
    )

    signature_params = [
        nonce,
        npc["characteristics"]["age"],  # type: ignore[index]
        npc["characteristics"]["role"],  # type: ignore[index]
        npc["characteristics"]["sex"],  # type: ignore[index]
        npc["character_trait"],  # type: ignore[index]
        npc["full_name"],  # type: ignore[index]
    ]
    signature = sign_parameters(signature_params, config.env["LOREMACHINE_PRIVATE_KEY"])

    return (npc, [str(signature[0]), str(signature[1])])


def spawn_npc(data: NpcSpawnMsgData, config: BootConfig) -> tuple[NpcProfile, list[str]]:
    llm = Llm()
    npc_db = NpcDatabase.instance()

    realm_entity_id = data["realm_entity_id"]
    npc_profile = npc_db.fetch_npc_profile_by_realm_entity_id(realm_entity_id)
    if npc_profile is None:
        logger.info(f"Generating new npc profile for realm_entity_id {realm_entity_id}")
        npc_profile = llm.generate_npc_profile()
        npc_db.insert_npc_profile(realm_entity_id, npc_profile)
    else:
        logger.info(f"Existing npc profile found for realm_entity_id {realm_entity_id}")

    return build_response(realm_entity_id=realm_entity_id, npc=npc_profile, config=config)
