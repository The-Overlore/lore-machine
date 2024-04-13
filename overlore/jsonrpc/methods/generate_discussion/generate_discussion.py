import json
import logging

from jsonrpcserver import Error, InvalidParams, Result, Success

from overlore.errors import ErrorCodes
from overlore.jsonrpc.methods.generate_discussion.response import Context, DiscussionBuilder, MethodParams

logger = logging.getLogger("overlore")


async def generate_discussion(context: Context, params: MethodParams) -> Result:
    try:
        validated_params = MethodParams.model_validate_json(json.dumps(params), strict=True)  # noqa: TRY300
        if len(validated_params.user_input) == 0:
            return Error(ErrorCodes.INVALID_TOWN_HALL_INPUT.value, ErrorCodes.INVALID_TOWN_HALL_INPUT.name)

        logger.info(f"Generating a town hall for realm_entity_id: {validated_params.realm_entity_id}")

        return await handle_valid_input(context=context, params=validated_params)

    except ValueError as e:
        return InvalidParams(str(e))

    except RuntimeError as e:
        err = e.args[0]
        logger.error(f"Error occured while generating town hall: {err.value} - {err.name}")
        return Error(err.value, err.name)

    except Exception as e:
        print(e)


async def handle_valid_input(context: Context, params: MethodParams) -> Result:
    discussion_builder = await DiscussionBuilder.create(context=context, params=params)

    discussion_response = await discussion_builder.create_response()

    return Success(json.dumps(discussion_response))
