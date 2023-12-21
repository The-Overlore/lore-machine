from typing import Awaitable, Callable

from gql import Client, gql  # pip install --pre gql[websockets]
from gql.transport.websockets import WebsocketsTransport

TRANSFER_EVENT = "0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"
COMBAT_EVENT = "0x30f73782da72e6613eab4ee2cf2ebc3d75cb02d6dd8c537483bb2717a2afb57"

OnEventCallbackType = Callable[[dict], Awaitable[None]]


async def torii_event_sub(torii_service_endpoint: str, realm_entity_id: str, on_event_callback: OnEventCallbackType):
    transport = WebsocketsTransport(
        url=torii_service_endpoint,
        # Uncomment the following lines to activate client pings
        # ping_interval=60,
        # pong_timeout=10,
    )

    client = Client(transport=transport)
    # first star is for event kind,
    # second star is for realm entity id
    # not sure what the third star is
    async with client as session:
        subscription = gql(
            """
          subscription {
          eventEmitted(keys: ["*", "*", "*"]) {
            id
            keys
            data
            createdAt
          }
        }
            """
        )

        async for result in session.subscribe(subscription):
            on_event_callback(result)
