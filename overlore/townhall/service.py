import asyncio
import functools
import json
import os
import signal
from types import FrameType

from dotenv import load_dotenv
from websockets import WebSocketServerProtocol, serve

from overlore.graphql.constants import Subscriptions
from overlore.graphql.event import process_event, torii_event_sub
from overlore.sqlite.events_db import EventsDatabase
from overlore.townhall.logic import gen_townhall
from overlore.utils import parse_cli_args

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

SERVICE_WS_PORT = 8766
# TODO: have a way to differentiate dev/prod config
TORII_WS = os.environ.get("DEV_TORII_WS")
TORII_GRAPHQL = os.environ.get("DEV_TORII_GRAPHQL")

args = parse_cli_args()


def handle_sigint(_signum: int, _b: FrameType | None) -> None:
    exit(0)


async def service(websocket: WebSocketServerProtocol, extra_argument: dict[str, bool]) -> None:
    async for message in websocket:
        if message is None:
            continue

        response = await gen_townhall(str(message), extra_argument["mock"])
        await websocket.send(json.dumps(response))


async def start() -> None:
    global OPENAI_API_KEY
    if OPENAI_API_KEY is None:
        OPENAI_API_KEY = "OpenAI API Key"
    if TORII_WS is None:
        raise RuntimeError("Failure to provide WS url")

    events_db = EventsDatabase.instance().init()

    signal.signal(signal.SIGINT, handle_sigint)

    bound_handler = functools.partial(service, extra_argument={"mock": args.mock})
    overlore_pulse = serve(bound_handler, args.address, SERVICE_WS_PORT)

    print(f"great job, starting this service on port {SERVICE_WS_PORT}. everything is perfect from now on.")
    await asyncio.gather(
        overlore_pulse,
        torii_event_sub(TORII_WS, process_event_bound_handler, Subscriptions.COMBAT_OUTCOME_EVENT_EMITTED),
        torii_event_sub(TORII_WS, process_event_bound_handler, Subscriptions.ORDER_ACCEPTED_EVENT_EMITTED),
    )


# hardcode for now, when more mature we need some plumbing to read this off a config
def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
