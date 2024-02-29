import asyncio
import functools
import json
import time
from threading import Thread

import pytest
import responses
import websockets

from overlore.config import BootConfig
from overlore.graphql.subscriptions import process_received_event
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.mocks import MOCK_KATANA_RESPONSE
from overlore.ws import handle_client_connection


# Function to run the torii mock in a separate thread
def run_lore_machine():
    OpenAIHandler.instance().init("")
    # Initialize our dbs
    _vector_db = VectorDatabase.instance().init(":memory:")
    _events_db = EventsDatabase.instance().init(":memory:")
    config = BootConfig()
    config.mock = True
    config.port = 8766
    config.env["KATANA_URL"] = "https://localhost:8080"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x64", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )

    bound_handler = functools.partial(handle_client_connection, config=config)
    start_server = websockets.serve(bound_handler, "localhost", config.port)  # Specify a fixed port

    loop.run_until_complete(start_server)
    loop.run_forever()


@pytest.fixture(scope="module")
def setup():
    # Start the Torii server in a separate thread
    server_thread = Thread(target=run_lore_machine, daemon=True)
    server_thread.start()
    yield
    # Cleanup code here if needed


@pytest.mark.asyncio
async def test_mock_response(setup):
    test_url = "https://localhost:8080"
    mock_response = json.dumps(MOCK_KATANA_RESPONSE)

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.POST, test_url, body=mock_response, status=200)
        time.sleep(1)
        async with websockets.connect("ws://localhost:8766") as websocket:
            await websocket.send('{"msg_type": 0, "data": {"realm_id": 1, "order_id": 1}}')
            actual = await websocket.recv()
            print(actual)
            actual_msg = json.loads(actual)["data"]["townhall"]
            actual_msg = actual_msg.replace("\n", "")
            expected = "Paul: Hello WorldNancy:Yes, Hello World indeed!"
            assert actual_msg == expected
