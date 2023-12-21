# graphql-ws is supported from gql version 3.0.0b0
from gql import Client, gql  # pip install --pre gql[websockets]
from gql.transport.websockets import WebsocketsTransport


async def main():
    transport = WebsocketsTransport(
        url="ws://localhost:4000/graphql",
        # Uncomment the following lines to activate client pings
        # ping_interval=60,
        # pong_timeout=10,
    )

    client = Client(transport=transport)

    async with client as session:
        # GraphQL query
        query = gql("{hello}")

        result = await session.execute(query)
        print(result)

        # GraphQL subscription
        subscription = gql(
            """
            subscription {
              greetings
            }
        """
        )

        async for result in session.subscribe(subscription):
            print(result)


# asyncio.run(main())
