import logging

from overlore.graphql.parsing import parse_event
from overlore.graphql.query import Queries, run_torii_query
from overlore.sqlite.events_db import EventsDatabase
from overlore.types import ToriiDataNode

logger = logging.getLogger("overlore")


def store_synced_events(events: list[ToriiDataNode]) -> None:
    events_db = EventsDatabase.instance()
    for event in events:
        parsed_event = parse_event(event=event)
        events_db.insert_event(event=parsed_event)


def get_synced_events(torii_endpoint: str, query: str) -> list[ToriiDataNode]:
    query_results = run_torii_query(torii_endpoint=torii_endpoint, query=query)
    events = [query_result["node"] for query_result in query_results["events"]["edges"]]
    return events


async def torii_boot_sync(torii_service_endpoint: str) -> None:
    store_synced_events(
        events=get_synced_events(torii_endpoint=torii_service_endpoint, query=Queries.ORDER_ACCEPTED_EVENT_QUERY.value),
    )
    store_synced_events(
        events=get_synced_events(torii_endpoint=torii_service_endpoint, query=Queries.COMBAT_OUTCOME_EVENT_QUERY.value),
    )
