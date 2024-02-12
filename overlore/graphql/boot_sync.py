import logging
from typing import cast

import requests

from overlore.graphql.constants import Queries
from overlore.graphql.parsing import parse_event
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
        events_db.insert_event(event=parsed_event, only_if_not_present=True)


def get_synced_events(torii_service_endpoint: str, query: str) -> list[SyncEvents]:
    data = None
    try:
        response = requests.post(torii_service_endpoint, json={"query": query}, timeout=5)
        json_response = response.json()
        data = json_response["data"]
    except KeyError as e:
        logger.error("KeyError accessing %s in JSON response: %s", e, json_response)
    if data is None:
        raise RuntimeError(f"Couldn't sync with Torii at boot {json_response['errors']}")
    edges = data["events"]["edges"]
    return cast(list[SyncEvents], edges)


async def torii_boot_sync(torii_service_endpoint: str) -> None:
    store_synced_events(
        get_synced_events(torii_service_endpoint=torii_service_endpoint, query=Queries.ORDER_ACCEPTED_EVENT_QUERY.value)
    )
    store_synced_events(
        get_synced_events(torii_service_endpoint=torii_service_endpoint, query=Queries.COMBAT_OUTCOME_EVENT_QUERY.value)
    )
