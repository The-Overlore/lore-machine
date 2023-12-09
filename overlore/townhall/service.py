import asyncio
import os

from dotenv import load_dotenv
from websockets import WebSocketServerProtocol, serve

from overlore.prompts.prompts import GptInterface
from overlore.townhall.logic import gen_townhall

WS_PORT = 8765
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDINGS_API_KEY = ""


async def service(websocket: WebSocketServerProtocol, path: str):
    async for message in websocket:
        response = await gen_townhall(message)
        await websocket.send(response)


# hardcode for now, when more mature we need some plumbing to read this off a config
async def main():
    gpt_interface = GptInterface.instance()
    print(OPENAI_API_KEY)
    gpt_interface.init(OPENAI_API_KEY, OPENAI_EMBEDDINGS_API_KEY)
    print(f"great job, starting this service on port {WS_PORT}. everything is perfect from now on.")
    async with serve(service, "localhost", WS_PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
