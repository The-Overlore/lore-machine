import asyncio
import functools
import json
import logging
import signal
from types import FrameType

from websockets import WebSocketServerProtocol, serve
from websockets.exceptions import ConnectionClosedError

from overlore.config import Config
from overlore.graphql.constants import Subscriptions
from overlore.graphql.event import process_event, torii_boot_sync, torii_subscription_connection
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.logic import handle_townhall_request
from overlore.utils import is_valid_message

logger = logging.getLogger("overlore")

EVENT_SUBS = [Subscriptions.COMBAT_OUTCOME_EVENT_EMITTED, Subscriptions.ORDER_ACCEPTED_EVENT_EMITTED]


async def prompt_loop(config: Config) -> None:
    while True:
        txt = input("hit enter to generate townhall with realm_id 73 or enter realm_id\n")
        realm_id = 73 if len(txt) == 0 else int(txt)
        msg = f'{{"realm_id": {realm_id}, "order": 1}}'
        (rowid, townhall, systemPrompt, userPrompt) = await handle_townhall_request(msg, config)
        logger.debug(f"______System prompt______\n{systemPrompt}\n________________________")
        logger.debug(f"______User prompt______\n{userPrompt}\n________________________")
        logger.debug(f"______GPT answer______\n{townhall}\n________________________\n\n\n\n\n\n\n\n")


async def cancel_all_tasks() -> None:
    subscriptions_names = [sub.name for sub in EVENT_SUBS]
    tasks = [task for task in asyncio.all_tasks() if task.get_name() in subscriptions_names]
    for task in tasks:
        logger.info(f"Cancelling task: {task.get_name()}")
        task.cancel()


def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
    logger.info("Shutting down Overlore ...")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    asyncio.run_coroutine_threadsafe(cancel_all_tasks(), loop=asyncio.get_running_loop())


def parse_and_validate_message(message: str) -> (bool, dict):
    """
    Parses the incoming WebSocket message and validates its signature.

    Args:
        message (str): The incoming WebSocket message in JSON format.

    Returns:
        bool: True if the message is valid, False otherwise.
        dict: The parsed payload if the message is valid, empty dict otherwise.
    """
    try:
        # Attempt to parse the incoming JSON message
        parsed_message = json.loads(message)
        payload = parsed_message["payload"]
        signature = parsed_message["signature"]  # Expected to be a list of integers
        public_key = parsed_message["public_key"]  # Expected to be an integer

        # Validate the message signature
        is_valid = is_valid_message(payload, signature, public_key)

    # TODO: sanity check starknet-py's error cases for message signature verification
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        # If there's an error during message parsing or validation
        logger.warning(f"Message parsing/validation error: {error}")
        return False, {}
    else:
        # linter demands an else case, even w/ an early return in try block
        # life is unfair
        return is_valid, payload if is_valid else {}


async def service(websocket: WebSocketServerProtocol, config: Config) -> None:
    async for message in websocket:
        if message is None:
            continue

        # Use the new function to parse and validate the message
        is_valid, payload = parse_and_validate_message(message)

        logger.debug("generating townhall")
        # convert message to string instead of bytes
        message_str = str(message)
        (rowid, response, _, _) = await handle_townhall_request(message_str, config)
        logger.debug(response)
        await websocket.send(json.dumps({rowid: response}))


async def start() -> None:
    config = Config()

    signal.signal(signal.SIGINT, handle_sigint)

    EventsDatabase.instance().init()

    VectorDatabase.instance().init()
    OpenAIHandler.instance().init(config.OPENAI_API_KEY)

    if config.prompt:
        await prompt_loop(config)

    # Sync events database on boot
    await torii_boot_sync(config.TORII_GRAPHQL)

    service_bound_handler = functools.partial(service, config=config)
    overlore_server = await serve(service_bound_handler, config.address, config.port)
    logger.info(f"great job, starting this service on port {config.port}. everything is perfect from now on.")
    try:
        await torii_subscription_connection(
            config.TORII_WS,
            process_event,
            EVENT_SUBS,
        )
    except ConnectionClosedError:
        logger.warning("Connection close on Torii, need to reconnect here")
    finally:
        overlore_server.close()
        await overlore_server.wait_closed()


# hardcode for now, when more mature we need some plumbing to read this off a config
def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
