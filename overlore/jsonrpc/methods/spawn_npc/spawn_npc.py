import json
import logging

from guardrails import Guard
from jsonrpcserver import Error, InvalidParams, Result, Success, method

from overlore.config import global_config
from overlore.jsonrpc.methods.spawn_npc.response import MethodParams, NpcProfileBuilder
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.torii.client import ToriiClient
from overlore.types import NpcProfile

logger = logging.getLogger("overlore")


@method
async def spawn_npc(params: MethodParams) -> Result:
    try:
        MethodParams.model_validate_json(json.dumps(params), strict=True)
    except ValueError as e:
        return InvalidParams(str(e))

    logger.info(f"Realm (entity_id: {params['realm_entity_id']}) requested spawn of NPC")  # type: ignore[index]
    try:
        return await handle_regular_flow(params=params)
    except RuntimeError as e:
        err = e.args[0]
        return Error(err.value, err.name)


async def handle_regular_flow(params: MethodParams) -> Result:
    guard = Guard.from_pydantic(output_class=NpcProfile, num_reasks=1)
    llm_client = AsyncOpenAiClient()
    torii_client = ToriiClient(url=global_config.env["TORII_GRAPHQL"])
    katana_client = KatanaClient(url=global_config.env["KATANA_URL"])
    npc_profile_builder = NpcProfileBuilder(
        llm_client=llm_client,
        torii_client=torii_client,
        katana_client=katana_client,
        lore_machine_pk=global_config.env["LOREMACHINE_PRIVATE_KEY"],
        guard=guard,
    )
    response = await npc_profile_builder.build_from_request_params(params=params)
    return Success(json.dumps(response))
