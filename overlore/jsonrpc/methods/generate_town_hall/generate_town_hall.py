import json
import logging
from typing import TypedDict

from guardrails import Guard
from jsonrpcserver import Error, InvalidParams, Result, Success

from overlore.jsonrpc.methods.generate_town_hall.response import MethodParams, TownHallBuilder
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.torii.client import ToriiClient

logger = logging.getLogger("overlore")


class Context(TypedDict):
    guard: Guard
    llm_client: AsyncOpenAiClient
    torii_client: ToriiClient
    katana_client: KatanaClient


async def generate_town_hall(context: Context, params: MethodParams) -> Result:
    try:
        MethodParams.model_validate_json(json.dumps(params), strict=True)
    except Exception as e:
        return InvalidParams(str(e))

    logger.info(f"Generating a town hall for realm_entity_id: {params['realm_entity_id']}")  # type: ignore[index]
    try:
        return await handle_regular_flow(context=context, params=params)
    except RuntimeError as e:
        err = e.args[0]
        return Error(err.value, err.name)


async def handle_regular_flow(context: Context, params: MethodParams) -> Result:
    town_hall_builder = TownHallBuilder(
        llm_client=context["llm_client"],
        torii_client=context["torii_client"],
        katana_client=context["katana_client"],
        guard=context["guard"],
    )

    townhall_response = await town_hall_builder.build_from_request_params(params=params)

    return Success(json.dumps(townhall_response))
