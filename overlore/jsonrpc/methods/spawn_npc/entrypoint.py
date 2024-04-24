import json
import logging
from json import JSONEncoder
from typing import Any

from jsonrpcserver import Error, InvalidParams, Result, Success

from overlore.jsonrpc.methods.spawn_npc.response import Context, MethodParams, NpcProfileBuilder, RandGenerator
from overlore.types import Backstory

logger = logging.getLogger("overlore")


class CustomEncoder(JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Backstory):
            return obj.model_dump()
        return JSONEncoder.default(self, obj)


async def spawn_npc(context: Context, params: MethodParams) -> Result:
    try:
        validated_params = MethodParams.model_validate_json(json.dumps(params), strict=True)  # noqa: TRY300
        logger.info(f"Realm (entity_id: {validated_params.realm_entity_id}) requested spawn of villager")
        return await handle_regular_flow(context=context, params=validated_params)

    except ValueError as e:
        return InvalidParams(str(e))

    except RuntimeError as e:
        err = e.args[0]
        return Error(err.value, err.name)


async def handle_regular_flow(context: Context, params: MethodParams) -> Result:
    npc_profile_builder = NpcProfileBuilder(context=context, params=params, rand_generator=RandGenerator())
    response = await npc_profile_builder.create_response()

    return Success(json.dumps(response, cls=CustomEncoder))
