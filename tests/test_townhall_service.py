import asyncio
import functools
import time
from threading import Thread

import pytest
import websockets

from overlore.graphql.event import process_event
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.service import service


# Function to run the server in a separate thread
def run_server():
    # Initialize our dbs
    _vector_db = VectorDatabase.instance().init(":memory:")
    _events_db = EventsDatabase.instance().init(":memory:")
    OpenAIHandler.instance().init("")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x6", "0x5", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        }
    )

    bound_handler = functools.partial(service, extra_argument={"mock": True})
    start_server = websockets.serve(bound_handler, "localhost", 8766)  # Specify a fixed port

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
async def test_mock_response(server):
    time.sleep(1)
    async with websockets.connect("ws://localhost:8766") as websocket:
        test_message = '{"realm_id": 1}'
        await websocket.send(test_message)
        actual = await websocket.recv()
        expected = """\"Paul: Friends, we must not lose sight of what keeps us afloat. Straejelas depends on both wheat and minerals.
        James: But Paul, look at the gold we can get for just a grain of our wheat!
        Lisa: Yes, we should be investing more in our mining initiatives.
        Paul: While I agree that deal is superficially advantageous, we traded a mountain of wheat for practically nothing earlier today. We need a balanced approach.
        Daniel: You farmers just want more for yourselves, bloated with gluttony and greed.
        Nancy: That's unfair, Daniel! We are all working for the benefit of Straejelas. We are happy as a realm and must remain united against threats, be it hunger or outside forces.
        Paul: Exactly, Nancy. The strength and happiness of our realm resides in the balance of our efforts. Walking the path of greed will only lead us to ruin. We cannot sacrifice our self-sustainability in the name of temporary wealth.
        James: Maybe you're right, Paul. As long as we are safe and fed, the gold is just a bonus. We should indeed be more mindful about our trades.
        Paul: That's the spirit, James. Together, we'll keep Straejelas thriving and prosperous.\""""
        actual_trimed = "".join(actual.split())
        actual_trimed = actual_trimed.replace("\\n\\n", "")
        expected_trimed = "".join(expected.split())
        assert actual_trimed == expected_trimed
