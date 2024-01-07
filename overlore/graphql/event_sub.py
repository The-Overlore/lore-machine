from typing import Callable

from gql import Client, gql  # pip install --pre gql[websockets]
from gql.transport.websockets import WebsocketsTransport

from overlore.graphql.constants import Subscriptions

OnEventCallbackType = Callable[[dict], int]


async def torii_event_sub(
    torii_service_endpoint: str, on_event_callback: OnEventCallbackType, subscription: Subscriptions
) -> None:
    transport = WebsocketsTransport(url=torii_service_endpoint)

    client = Client(transport=transport)
    async with client as session:
        gql_subscription = gql(subscription.value)

        async for result in session.subscribe(gql_subscription):
            try:
                on_event_callback(result)
            except RuntimeError:
                print("Unable to process event")
