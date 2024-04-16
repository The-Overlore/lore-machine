import json
import logging

from jsonrpcserver import Error, InvalidParams, Result, Success

from overlore.jsonrpc.methods.get_npc_backstory.response import Context, MethodParams, NpcBackstoryGetter

logger = logging.getLogger("overlore")


async def get_npc_backstory(context: Context, params: MethodParams) -> Result:
    try:
        validated_params = MethodParams.model_validate_json(json.dumps(params), strict=True)  # noqa: TRY300

        return await handle_valid_input(context=context, params=validated_params)

    except ValueError as e:
        return InvalidParams(str(e))

    except RuntimeError as e:
        err = e.args[0]
        logger.error(f"Error occured while generating discussion: {err.value} - {err.name}")
        return Error(err.value, err.name)

    except Exception as e:
        logger.info(e)


async def handle_valid_input(context: Context, params: MethodParams) -> Result:
    npc_backstory_getter: NpcBackstoryGetter = NpcBackstoryGetter.create(context=context, params=params)

    discussion_response = npc_backstory_getter.create_response()

    return Success(json.dumps(discussion_response))
