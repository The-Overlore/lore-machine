from typing import Callable, cast

from gql import Client, gql  # pip install --pre gql[websockets]
from gql.transport.websockets import WebsocketsTransport

from overlore.eternum.constants import Realms
from overlore.eternum.types import AttackingEntityIds, ResourceAmounts
from overlore.graphql.constants import EventType as EventKeyHash
from overlore.graphql.constants import Subscriptions
from overlore.sqlite.constants import EventType as SqLiteEventType
from overlore.sqlite.events_db import EventsDatabase
from overlore.townhall.logic import get_combat_outcome_importance, get_trade_importance
from overlore.types import EventData, EventKeys, ParsedEvent, ToriiEvent

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


def parse_combat_outcome_event(realms: Realms, keys: EventKeys, data: EventData) -> ParsedEvent:
    attacker_realm_id = int(keys[1], base=16)
    target_realm_entity_id = int(keys[2], base=16)

    (data, attacking_entity_ids) = parse_attacking_entity_ids(data)
    (data, stolen_resources) = parse_resources(data)

    winner = int(data[0], base=16)
    damage = int(data[1], base=16)
    ts = int(data[2], base=16)

    importance = get_combat_outcome_importance(stolen_resources=stolen_resources, damage=damage)
    parsed_event: ParsedEvent = {
        "type": SqLiteEventType.COMBAT_OUTCOME.value,
        "active_pos": realms.position_by_id(attacker_realm_id),
        "passive_pos": realms.position_by_id(target_realm_entity_id),
        "attacking_entity_ids": attacking_entity_ids,
        "stolen_resources": stolen_resources,
        "winner": winner,
        "damage": damage,
        "importance": importance,
        "ts": ts,
    }
    return parsed_event


def parse_trade_event(realms: Realms, keys: EventKeys, data: EventData) -> ParsedEvent:
    _trade_id = int(keys[1], base=16)
    maker_id = int(data[0], base=16)
    taker_id = int(data[1], base=16)

    data = data[2:]

    (data, resources_maker) = parse_resources(data)
    (data, resources_taker) = parse_resources(data)
    ts = int(data[0], base=16)

    importance = get_trade_importance(resources_maker + resources_taker)

    parsed_event: ParsedEvent = {
        "type": SqLiteEventType.ORDER_ACCEPTED.value,
        "active_pos": realms.position_by_id(maker_id),
        "passive_pos": realms.position_by_id(taker_id),
        "resources_maker": resources_maker,
        "resources_taker": resources_taker,
        "importance": importance,
        "ts": ts,
    }
    return parsed_event


def process_event(
    event: ToriiEvent,
    events_db: EventsDatabase,
) -> int:
    event_emitted = event.get("eventEmitted")
    if not event_emitted:
        raise RuntimeError("eventEmitted no present in event")
    keys = cast(EventKeys, event_emitted.get("keys"))
    if not keys:
        raise RuntimeError("Event had no keys")
    data = cast(EventData, event_emitted.get("data"))
    if not data:
        raise RuntimeError("Event had no data")
    if get_event_type(keys=keys) == EventKeyHash.COMBAT_OUTCOME.value:
        parsed_event = parse_combat_outcome_event(realms=events_db.realms, keys=keys, data=data)
    else:
        parsed_event = parse_trade_event(realms=events_db.realms, keys=keys, data=data)
    added_id: int = events_db.insert_event(parsed_event)
    return added_id
