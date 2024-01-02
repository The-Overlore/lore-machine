from typing import Awaitable, Callable

from gql import Client, gql  # pip install --pre gql[websockets]
from gql.transport.websockets import WebsocketsTransport

from overlore.graphql.constants import Subscriptions

OnEventCallbackType = Callable[[dict], Awaitable[None]]


async def torii_event_sub(
    torii_service_endpoint: str, on_event_callback: OnEventCallbackType, subscription: Subscriptions
):
    transport = WebsocketsTransport(url=torii_service_endpoint)

    client = Client(transport=transport)
    async with client as session:
        gql_subscription = gql(subscription.value)

        async for result in session.subscribe(gql_subscription):
            on_event_callback(result)
