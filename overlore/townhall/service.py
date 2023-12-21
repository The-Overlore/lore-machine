import argparse
import asyncio
import json
import os
import signal

from dotenv import load_dotenv
from websockets import WebSocketServerProtocol, serve

from overlore.graphql.event_sub import torii_event_sub
from overlore.prompts.prompts import GptInterface
from overlore.townhall.logic import gen_townhall

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDINGS_API_KEY = ""

SERVICE_WS_PORT = 8766
# TODO: have a way to differentiate dev/prod config
TORII_WS = os.environ.get("DEV_TORII_WS")
TORII_GRAPHQL = os.environ.get("DEV_TORII_GRAPHQL")


def simple_callback(argument):
    print(argument)


parser = argparse.ArgumentParser(description="The weaving loomer of all possible actual experiential occasions.")
parser.add_argument(
    "--mock",
    action="store_true",
    help="Use mock data for GPT response instead of querying the API. (saves API calls)",
)
parser.add_argument("-a", "--address", help="Host address for connection", type=str, default="localhost")

args = parser.parse_args()


def handle_sigint(a, b):
    exit(0)


async def service(websocket: WebSocketServerProtocol, path: str):
    async for message in websocket:
        response = await gen_townhall(message, args.mock)
        await websocket.send(json.dumps(response))


async def start():
    signal.signal(signalnum=signal.SIGINT, handler=handle_sigint)
    gpt_interface = GptInterface.instance()
    gpt_interface.init(OPENAI_API_KEY, OPENAI_EMBEDDINGS_API_KEY)
    overlore_pulse = serve(service, "localhost", SERVICE_WS_PORT)
    print(f"great job, starting this service on port {SERVICE_WS_PORT}. everything is perfect from now on.")
    # arbitrarily choose just the first realm to sub to events on
    await asyncio.gather(overlore_pulse, torii_event_sub(TORII_WS, simple_callback))


# hardcode for now, when more mature we need some plumbing to read this off a config
def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
