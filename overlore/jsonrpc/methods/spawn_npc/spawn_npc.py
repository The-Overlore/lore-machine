import json
import logging
from typing import TypedDict

from jsonrpcserver import Error, InvalidParams, Result, Success

from overlore.jsonrpc.methods.spawn_npc.response import MethodParams, NpcProfileBuilder
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.llm.guard import AsyncGuard
from overlore.torii.client import ToriiClient

logger = logging.getLogger("overlore")


class Context(TypedDict):
    guard: AsyncGuard
    llm_client: AsyncOpenAiClient
    torii_client: ToriiClient
    katana_client: KatanaClient
    lore_machine_pk: str


async def spawn_npc(context: Context, params: MethodParams) -> Result:
    try:
        MethodParams.model_validate_json(json.dumps(params), strict=True)
    except ValueError as e:
        return InvalidParams(str(e))

    logger.info(f"Realm (entity_id: {params['realm_entity_id']}) requested spawn of NPC")  # type: ignore[index]
    try:
        return await handle_regular_flow(context=context, params=params)
    except RuntimeError as e:
        err = e.args[0]
        return Error(err.value, err.name)


async def handle_regular_flow(context: Context, params: MethodParams) -> Result:
    npc_profile_builder = NpcProfileBuilder(
        llm_client=context["llm_client"],
        torii_client=context["torii_client"],
        katana_client=context["katana_client"],
        lore_machine_pk=context["lore_machine_pk"],
        guard=context["guard"],
    )
    response = await npc_profile_builder.build_from_request_params(params=params)
    return Success(json.dumps(response))
