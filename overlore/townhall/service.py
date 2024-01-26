import asyncio
import functools
import json
import signal
from types import FrameType

from websockets import WebSocketServerProtocol, serve
from websockets.exceptions import ConnectionClosedError

from overlore.graphql.constants import Subscriptions
from overlore.graphql.event import process_event, torii_boot_sync, torii_event_sub
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.logic import handle_townhall_request
from overlore.utils import OPENAI_API_KEY, TORII_GRAPHQL, TORII_WS, parse_cli_args

SERVICE_WS_PORT = 8766
args = parse_cli_args()


def handle_sigint(_signum: int, _b: FrameType | None) -> None:
    exit(0)


async def service(websocket: WebSocketServerProtocol, extra_argument: dict[str, bool]) -> None:
    async for message in websocket:
        if message is None:
            continue
        print("generating townhall")
        response = await handle_townhall_request(str(message), extra_argument["mock"])
        await websocket.send(json.dumps(response))


async def start() -> None:
    open_ai_api_key = ""
    open_ai_api_key = "OpenAI API Key" if OPENAI_API_KEY is None else OPENAI_API_KEY
    if TORII_WS is None:
        raise RuntimeError("Failure to provide WS url")
    if TORII_GRAPHQL is None:
        raise RuntimeError("Failure to provide WS url")

    signal.signal(signal.SIGINT, handle_sigint)

    EventsDatabase.instance().init()

    # Sync events database on boot
    await torii_boot_sync(TORII_GRAPHQL)

    VectorDatabase.instance().init()
    OpenAIHandler.instance().init(open_ai_api_key)

    service_bound_handler = functools.partial(service, extra_argument={"mock": args.mock})
    overlore_pulse = serve(service_bound_handler, args.address, SERVICE_WS_PORT)

    print(f"great job, starting this service on port {SERVICE_WS_PORT}. everything is perfect from now on.")
    try:
        await asyncio.gather(
            overlore_pulse,
            torii_event_sub(TORII_WS, process_event, Subscriptions.COMBAT_OUTCOME_EVENT_EMITTED),
            torii_event_sub(TORII_WS, process_event, Subscriptions.ORDER_ACCEPTED_EVENT_EMITTED),
        )
    except ConnectionClosedError:
        print("Connection close on Torii, need to reconnect here")


# hardcode for now, when more mature we need some plumbing to read this off a config
def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
