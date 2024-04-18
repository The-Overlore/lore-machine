import json
import logging

from jsonrpcserver import Error, InvalidParams, Result, Success

from overlore.jsonrpc.methods.get_discussions.response import Context, DiscussionGetter, MethodParams

logger = logging.getLogger("overlore")


async def get_discussions(context: Context, params: MethodParams) -> Result:
    try:
        validated_params = MethodParams.model_validate_json(  # noqa: TRY300
            json.dumps(params),
            strict=True,
        )

        return handle_valid_input(context=context, params=validated_params)

    except ValueError as e:
        return InvalidParams(str(e))

    except RuntimeError as e:
        err = e.args[0]
        logger.error(f"Error occured while getting discussions: {err.value} - {err.name}")
        return Error(err.value, err.name)

    except Exception as e:
        logger.info(e)


def handle_valid_input(context: Context, params: MethodParams) -> Result:
    discussion_getter = DiscussionGetter.create(context=context, params=params)

    discussion_response = discussion_getter.create_response()

    return Success(json.dumps(discussion_response))
