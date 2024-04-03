import json
import logging

from guardrails import Guard
from jsonrpcserver import Error, InvalidParams, Result, Success, method

from overlore.config import global_config
from overlore.jsonrpc.methods.generate_town_hall.response import MethodParams, TownHallBuilder
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.sqlite.events_db import EventsDatabase
from overlore.torii.client import ToriiClient
from overlore.types import Townhall

logger = logging.getLogger("overlore")


@method
async def generate_town_hall(params: MethodParams) -> Result:
    try:
        MethodParams.model_validate_json(json.dumps(params), strict=True)
    except Exception as e:
        return InvalidParams(str(e))

    logger.info(f"Generating a town hall for realm_entity_id: {params['realm_entity_id']}")  # type: ignore[index]
    try:
        return await handle_regular_flow(params=params)
    except RuntimeError as e:
        err = e.args[0]
        return Error(err.value, err.name)


async def handle_regular_flow(params: MethodParams) -> Result:
    guard = Guard.from_pydantic(output_class=Townhall, num_reasks=0)
    llm_client = AsyncOpenAiClient()
    torii_client = ToriiClient(url=global_config.env["TORII_GRAPHQL"], events_db=EventsDatabase.instance())
    katana_client = KatanaClient(url=global_config.env["KATANA_URL"])
    town_hall_builder = TownHallBuilder(
        llm_client=llm_client, torii_client=torii_client, katana_client=katana_client, guard=guard
    )

    townhall_response = await town_hall_builder.build_from_request_params(params=params)

    return Success(json.dumps(townhall_response))
