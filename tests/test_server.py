import pytest
import asyncio
import websockets
from threading import Thread
from overlore.server import echo 

# Function to run the server in a separate thread
def run_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(echo, "localhost", 8767)  # Specify a fixed port
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
        test_message = "Hello WebSocket"
        await websocket.send(test_message)
        response = await websocket.recv()
        assert response == test_message
