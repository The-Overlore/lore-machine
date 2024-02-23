from typing import cast

from overlore.eternum.constants import Realms
from overlore.eternum.types import AttackingEntityIds, ResourceAmounts
from overlore.graphql.constants import EventType as EventKeyHash
from overlore.sqlite.constants import EventType as SqLiteEventType
from overlore.townhall.logic import get_combat_outcome_importance, get_trade_importance
from overlore.types import EventData, EventKeys, ParsedEvent, ToriiEvent


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
    attacker_realm_id = int(keys[2], base=16)
    target_realm_entity_id = int(keys[3], base=16)
    target_realm_id = int(keys[4], base=16)

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
        "active_realm_id": attacker_realm_id,
        "passive_realm_entity_id": target_realm_entity_id,
        "passive_realm_id": target_realm_id,
        "active_pos": realms.position_by_id(attacker_realm_id),
        "passive_pos": realms.position_by_id(target_realm_id),
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
    maker_realm_id = int(data[1], base=16)
    taker_realm_entity_id = int(data[2], base=16)
    taker_realm_id = int(data[3], base=16)

    resources_index_start = 4
    data = data[resources_index_start:]

    (data, resources_maker) = parse_resources(data)
    (data, resources_taker) = parse_resources(data)
    ts = int(data[0], base=16)

    importance = get_trade_importance(resources_maker + resources_taker)

    parsed_event: ParsedEvent = {
        "torii_event_id": torii_event_id,
        "type": SqLiteEventType.ORDER_ACCEPTED.value,
        "active_realm_entity_id": taker_realm_entity_id,
        "active_realm_id": taker_realm_id,
        "passive_realm_entity_id": maker_realm_entity_id,
        "passive_realm_id": maker_realm_id,
        "active_pos": realms.position_by_id(taker_realm_id),
        "passive_pos": realms.position_by_id(maker_realm_id),
        "resources_maker": resources_maker,
        "resources_taker": resources_taker,
        "importance": importance,
        "ts": ts,
    }
    return parsed_event


def parse_event(event: ToriiEvent) -> ParsedEvent:
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
