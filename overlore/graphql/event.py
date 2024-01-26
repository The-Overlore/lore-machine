import logging
from copy import deepcopy
from typing import Callable, cast

import requests
from gql import Client, gql  # pip install --pre gql[websockets]
from gql.transport.websockets import WebsocketsTransport

from overlore.eternum.constants import Realms
from overlore.eternum.types import AttackingEntityIds, ResourceAmounts
from overlore.graphql.constants import EventType as EventKeyHash
from overlore.graphql.constants import Queries, Subscriptions
from overlore.sqlite.constants import EventType as SqLiteEventType
from overlore.sqlite.events_db import EventsDatabase
from overlore.townhall.logic import get_combat_outcome_importance, get_trade_importance
from overlore.types import EventData, EventKeys, ParsedEvent, RawToriiEvent, SubEvents, SyncEvents

logger = logging.getLogger("overlore")

OnEventCallbackType = Callable[[dict], int]


def store_synced_events(events: list[SyncEvents]) -> None:
    events_db = EventsDatabase.instance()
    for event in events:
        event_emitted = event.get("node")
        if not event_emitted:
            raise RuntimeError("node no present in event")
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
                logger.error("Unable to process event: %s", result)


def get_event_type(keys: EventKeys) -> str:
    return str(keys[0])


def parse_resources(data: list[str]) -> tuple[list[str], ResourceAmounts]:
    resource_len = int(data[0], base=16)
    end_idx_resources = resource_len * 2
    resources = [
        {"type": int(data[i], base=16), "amount": int(int(data[i + 1], base=16) / 1000)}
        for i in range(1, end_idx_resources, 2)
    ]
    return (data[end_idx_resources + 1 :], resources)


def parse_attacking_entity_ids(data: list[str]) -> tuple[list[str], AttackingEntityIds]:
    length = int(data[0], base=16)
    attacking_entity_ids = [int(data[i], base=16) for i in range(1, length)]
    return (data[1 + length :], attacking_entity_ids)


def parse_combat_outcome_event(torii_event_id: str, keys: EventKeys, data: EventData) -> ParsedEvent:
    realms = Realms.instance()

    attacker_realm_entity_id = int(keys[1], base=16)
    target_realm_entity_id = int(keys[2], base=16)

    (data, attacking_entity_ids) = parse_attacking_entity_ids(data)
    (data, stolen_resources) = parse_resources(data)

    winner = int(data[0], base=16)
    damage = int(data[1], base=16)
    ts = int(data[2], base=16)

    importance = get_combat_outcome_importance(stolen_resources=stolen_resources, damage=damage)
    parsed_event: ParsedEvent = {
        "torii_event_id": torii_event_id,
        "type": SqLiteEventType.COMBAT_OUTCOME.value,
        "active_realm_entity_id": attacker_realm_entity_id,
        "passive_realm_entity_id": target_realm_entity_id,
        "active_pos": realms.position_by_id(attacker_realm_entity_id),
        "passive_pos": realms.position_by_id(target_realm_entity_id),
        "attacking_entity_ids": attacking_entity_ids,
        "stolen_resources": stolen_resources,
        "winner": winner,
        "damage": damage,
        "importance": importance,
        "ts": ts,
    }
    return parsed_event


def parse_trade_event(torii_event_id: str, keys: EventKeys, data: EventData) -> ParsedEvent:
    realms = Realms.instance()

    _trade_id = int(keys[1], base=16)
    maker_realm_entity_id = int(data[0], base=16)
    taker_realm_entity_id = int(data[1], base=16)

    data = data[2:]

    (data, resources_maker) = parse_resources(data)
    (data, resources_taker) = parse_resources(data)
    ts = int(data[0], base=16)

    importance = get_trade_importance(resources_maker + resources_taker)

    parsed_event: ParsedEvent = {
        "torii_event_id": torii_event_id,
        "type": SqLiteEventType.ORDER_ACCEPTED.value,
        "active_realm_entity_id": taker_realm_entity_id,
        "passive_realm_entity_id": maker_realm_entity_id,
        "active_pos": realms.position_by_id(maker_realm_entity_id),
        "passive_pos": realms.position_by_id(taker_realm_entity_id),
        "resources_maker": resources_maker,
        "resources_taker": resources_taker,
        "importance": importance,
        "ts": ts,
    }
    return parsed_event


def parse_event(event: RawToriiEvent) -> ParsedEvent:
    keys = cast(EventKeys, event.get("keys"))
    if not keys:
        raise RuntimeError("Event had no keys")
    data = cast(EventData, event.get("data"))
    if not data:
        raise RuntimeError("Event had no data")
    torii_event_id = cast(str, event.get("id"))
    if not torii_event_id:
        raise RuntimeError("Event had no torii_event_id")
    if get_event_type(keys=keys) == EventKeyHash.COMBAT_OUTCOME.value:
        parsed_event = parse_combat_outcome_event(torii_event_id=torii_event_id, keys=keys, data=data)
    else:
        parsed_event = parse_trade_event(torii_event_id=torii_event_id, keys=keys, data=data)

    return parsed_event


def process_event(
    event: SubEvents,
) -> int:
    events_db = EventsDatabase.instance()
    event_emitted = event.get("eventEmitted")
    if not event_emitted:
        raise RuntimeError("eventEmitted no present in event")

    parsed_event = parse_event(event=event_emitted)
    parsed_event_copy = deepcopy(parsed_event)
    added_id: int = events_db.insert_event(event=parsed_event, only_if_not_present=False)
    logger.info(f"Stored event received at rowid {added_id}: {parsed_event}")
    return added_id
