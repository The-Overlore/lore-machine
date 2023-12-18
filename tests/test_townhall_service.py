import asyncio
from threading import Thread

import pytest
import websockets

from overlore.townhall.service import service


# Function to run the server in a separate thread
def run_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(service, "localhost", 8767)  # Specify a fixed port
    loop.run_until_complete(start_server)
    loop.run_forever()


@pytest.fixture(scope="module")
def server():
    # Start the server in a separate thread
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    yield
    # Cleanup code here if needed


@pytest.mark.asyncio
async def test_echo(server):
    async with websockets.connect("ws://localhost:8767") as websocket:
        test_message = "townhall pls"
        await websocket.send(test_message)
        response = await websocket.recv()
        assert (
            response
            == "Users that all want to overthrow their lord: ['User1', 'User2', 'User3'], Events: ['Event1', 'Event2',"
            " 'Event3']"
        )
