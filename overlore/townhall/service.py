import argparse
import asyncio
import json
import os
import signal

from dotenv import load_dotenv
from websockets import WebSocketServerProtocol, serve

from overlore.prompts.prompts import GptInterface
from overlore.townhall.logic import gen_townhall

WS_PORT = 8765
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDINGS_API_KEY = ""

parser = argparse.ArgumentParser(description="Optional app description")
parser.add_argument(
    "--mock",
    action="store_true",
    help="Use mock data for GPT response instead of querying the API. (saves API calls)",
)
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
    print(f"great job, starting this service on port {WS_PORT}. everything is perfect from now on.")
    async with serve(service, "localhost", WS_PORT):
        await asyncio.Future()  # Run forever


# hardcode for now, when more mature we need some plumbing to read this off a config
def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
