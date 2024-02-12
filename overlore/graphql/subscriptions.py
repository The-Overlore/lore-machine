import asyncio
import logging
import sys
from typing import Callable

import backoff
from backoff._typing import Details
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport

from overlore.graphql.constants import Subscriptions
from overlore.graphql.parsing import parse_event
from overlore.sqlite.events_db import EventsDatabase
from overlore.types import ToriiEmittedEvent

logger = logging.getLogger("overlore")

OnEventCallbackType = Callable[[dict], int]


def backoff_logging(details: Details) -> None:
    # Retrieve exception type, value, and traceback
    exc_type, exc_value, _ = sys.exc_info()

    # Format the exception information for logging
    if exc_type is not None and exc_value is not None:
        exc_info = f"{exc_type.__name__}: {exc_value}"
    else:
        exc_info = "No exception information"

    # Format the exception information for logging
    logger.warning(
        "Backing off %s seconds after %s tries calling function %s with args %s and kwargs %s due to %s",
        details["wait"],
        details["tries"],
        details["target"].__name__,
        details["args"],
        details["kwargs"],
        exc_info,
    )


async def torii_event_sub(
    session: Client, on_event_callback: OnEventCallbackType, gql_subscription: Subscriptions
) -> None:
    logger.debug("subscribing to %s", gql_subscription)
    async for result in session.subscribe(gql(gql_subscription.value)):  # type: ignore[attr-defined]
        try:
            on_event_callback(result)
        except RuntimeError:
            logger.error("Unable to process event %s in %s", result, gql_subscription)


@backoff.on_exception(backoff.expo, Exception, max_time=300, on_backoff=backoff_logging)
async def torii_subscription_connection(
    torii_service_endpoint: str, callback_and_subs: list[tuple[Subscriptions, OnEventCallbackType]]
) -> None:
    transport = WebsocketsTransport(url=torii_service_endpoint)
    client = Client(transport=transport)
    logger.debug("attempting to establish subscription client...")
    async with client as session:
        tasks = [
            asyncio.create_task(torii_event_sub(session, callback, sub), name=sub.name)
            for (sub, callback) in callback_and_subs
        ]
        await asyncio.gather(*tasks)


def parse_and_store_event(
    event: ToriiEmittedEvent,
) -> int:
    events_db = EventsDatabase.instance()

    parsed_event = parse_event(event=event["eventEmitted"])
    added_id: int = events_db.insert_event(event=parsed_event, only_if_not_present=False)
    return added_id


def assign_name_character_trait_to_npc(event: ToriiEmittedEvent) -> int:
    return 19
