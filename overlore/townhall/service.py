import asyncio
import functools
import json
import signal
from types import FrameType

from websockets import WebSocketServerProtocol, serve
from websockets.exceptions import ConnectionClosedError

from overlore.config import Config
from overlore.graphql.constants import Subscriptions
from overlore.graphql.event import process_event, torii_boot_sync, torii_event_sub
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.logic import handle_townhall_request

global_shutdown_event = asyncio.Event()


def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
    print("\nShutting down, wait for a few seconds...")
    global_shutdown_event.set()


async def service(websocket: WebSocketServerProtocol, config: Config) -> None:
    while not global_shutdown_event.is_set():
        async for message in websocket:
            if message is None:
                continue
            print("generating townhall")
            response = await handle_townhall_request(str(message), config)
            await websocket.send(json.dumps(response))


async def start() -> None:
    config = Config()

    signal.signal(signal.SIGINT, handle_sigint)

    EventsDatabase.instance().init()

    # Sync events database on boot
    await torii_boot_sync(config.TORII_GRAPHQL)

    VectorDatabase.instance().init()
    OpenAIHandler.instance().init(config.OPENAI_API_KEY)

    service_bound_handler = functools.partial(service, config=config)
    overlore_pulse = await serve(service_bound_handler, config.address, config.port)
    combat_sub_task = asyncio.create_task(
        torii_event_sub(config.TORII_WS, process_event, Subscriptions.COMBAT_OUTCOME_EVENT_EMITTED)
    )
    order_sub_task = asyncio.create_task(
        torii_event_sub(config.TORII_WS, process_event, Subscriptions.ORDER_ACCEPTED_EVENT_EMITTED)
    )

    print(f"great job, starting this service on port {config.port}. everything is perfect from now on.")
    try:
        await global_shutdown_event.wait()
    except ConnectionClosedError:
        print("Connection close on Torii, need to reconnect here")
    finally:
        combat_sub_task.cancel()
        order_sub_task.cancel()
        overlore_pulse.close()
        await overlore_pulse.wait_closed()


# hardcode for now, when more mature we need some plumbing to read this off a config
def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
