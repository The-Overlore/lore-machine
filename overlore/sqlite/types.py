from typing import TypeAlias

from overlore.eternum.types import RealmPosition

# Stored event:
#  0      1     2                       3                        4           5   6         70         1          80          1
# [rowid, type, active_realm_entity_id, passive_realm_entity_id, importance, ts, metadata, (X_active, Y_active), (X_passive, Y_passive)]
# rowid: DB id of the event
# event_type: EventType (ORDER_ACCEPTED/COMBAT_OUTCOME)
# active_realm_entity_id: id of the active party in the action (taker of the trade, attacker of the combat)
# passive_realm_entity_id: id of the passive party in the action (maker of the trade, target of the combat)
# importance: generic importance score
# ts: Katana timestamp of the event
# active_pos: Position of the realm of the taker of the trade or the attacker of the combat
# active_pos: Position of the realm of the maker of the trade or the targer of the combat
# metadata:
#   for ORDER_ACCEPTED: {resources_maker: [{type: x, amount: y}, ...], resources_taker:  [{type: x, amount: y}, ...], }
#   for COMBAT_OUTCOME: {attacking_entity_ids: [id, ...], stolen_resources:  [{type: x, amount: y}, ...], winner: ATTACKER/TARGER, damage: x}
StoredEvent: TypeAlias = list[int | str | RealmPosition]

StoredVector: TypeAlias = tuple[int, float]

TownhallEventResponse: TypeAlias = tuple[int | str, bool]

StoredNpcProfile: TypeAlias = tuple[int, str, str, str, str]
"Realm_id, Name, Sex, Trait, Summary"
