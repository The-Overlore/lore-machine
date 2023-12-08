import asyncio

from websockets import WebSocketServerProtocol, serve

from overlore.townhall.logic import gen_townhall


async def service(websocket: WebSocketServerProtocol, path: str):
    async for _message in websocket:
        response = gen_townhall()
        await websocket.send(response)


# hardcode for now, when more mature we need some plumbing to read this off a config
async def main():
    async with serve(service, "localhost", 8765):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    print("great job, starting this service. everything is perfect from now on.")
    asyncio.run(main())
