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
from overlore.graphql.event import process_event, torii_boot_sync, torii_subscription_connection, torii_event_sub
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.logic import handle_townhall_request

global_shutdown_event = asyncio.Event()
logger = logging.getLogger("overlore")


async def prompt_loop(config: Config) -> None:
    while True:
        txt = input("hit enter to generate townhall with realm_id 73 or enter realm_id\n")
        realm_id = 73 if len(txt) == 0 else int(txt)
        msg = f'{{"realm_id": {realm_id}, "order": 1}}'
        (rowid, townhall, systemPrompt, userPrompt) = await handle_townhall_request(msg, config)
        logger.debug(f"______System prompt______\n{systemPrompt}\n________________________")
        logger.debug(f"______User prompt______\n{userPrompt}\n________________________")
        logger.debug(f"______GPT answer______\n{townhall}\n________________________\n\n\n\n\n\n\n\n")


async def shutdown() -> None:
    global_shutdown_event.set()


async def shutdown() -> None:
    global_shutdown_event.set()


def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
    print("\nShutting down Overlore ...")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    asyncio.run_coroutine_threadsafe(shutdown(), loop=asyncio.get_running_loop())
    # exit(0)


async def service(websocket: WebSocketServerProtocol, config: Config) -> None:
    while not global_shutdown_event.is_set():
        async for message in websocket:
            if message is None:
                continue
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

    # Old
    # overlore_pulse = serve(service_bound_handler, config.address, config.port)

    overlore_server = await serve(service_bound_handler, config.address, config.port)
    combat_sub_task = asyncio.create_task(
        torii_event_sub(config.TORII_WS, process_event, Subscriptions.COMBAT_OUTCOME_EVENT_EMITTED)
    )
    order_sub_task = asyncio.create_task(
        torii_event_sub(config.TORII_WS, process_event, Subscriptions.ORDER_ACCEPTED_EVENT_EMITTED)
    )

    logger.info(f"great job, starting this service on port {config.port}. everything is perfect from now on.")
    try:
        await global_shutdown_event.wait()
        # await asyncio.gather(
        #     overlore_pulse,
        #     torii_subscription_connection(
        #         config.TORII_WS,
        #         process_event,
        #         [Subscriptions.COMBAT_OUTCOME_EVENT_EMITTED, Subscriptions.ORDER_ACCEPTED_EVENT_EMITTED],
        #     ),
        # )
    except ConnectionClosedError:
        logger.warning("Connection close on Torii, need to reconnect here")
    finally:
        combat_sub_task.cancel()
        order_sub_task.cancel()
        overlore_server.close()
        await overlore_server.wait_closed()


# hardcode for now, when more mature we need some plumbing to read this off a config
def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
