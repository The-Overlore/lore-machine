import logging
from typing import cast

from overlore.graphql.constants import Queries
from overlore.graphql.parsing import parse_event
from overlore.graphql.query import run_torii_query
from overlore.sqlite.events_db import EventsDatabase
from overlore.types import SyncEvents

logger = logging.getLogger("overlore")


def store_synced_events(events: list[SyncEvents]) -> None:
    events_db = EventsDatabase.instance()
    for event in events:
        event_emitted = event.get("node")
        if not event_emitted:
            raise RuntimeError("node not present in event")
        parsed_event = parse_event(event=event_emitted)
        events_db.insert_event(event=parsed_event)


def get_synced_events(torii_endpoint: str, query: str) -> list[SyncEvents]:
    query_result = run_torii_query(torii_endpoint=torii_endpoint, query=query)
    edges = query_result["events"]["edges"]
    return cast(list[SyncEvents], edges)


async def torii_boot_sync(torii_service_endpoint: str) -> None:
    store_synced_events(
        events=get_synced_events(torii_endpoint=torii_service_endpoint, query=Queries.ORDER_ACCEPTED_EVENT_QUERY.value),
    )
    store_synced_events(
        events=get_synced_events(torii_endpoint=torii_service_endpoint, query=Queries.COMBAT_OUTCOME_EVENT_QUERY.value),
    )
