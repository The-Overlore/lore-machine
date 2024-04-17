from __future__ import annotations

import json
from typing import TypeAlias, TypedDict

from overlore.eternum.types import RealmPosition
from overlore.types import DialogueSegment, Discussion, NpcEntity

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


class StoredSegment(TypedDict):
    npc_entity_id: int
    segment: str


class StorableDiscussion(TypedDict):
    realm_id: int
    timestamp: int
    dialogue: list[StoredSegment]
    user_input: str
    input_score: int

    @classmethod  # type: ignore[misc]
    def from_llm_output(
        cls, realm_id: int, ts: int, discussion: Discussion, user_input: str, realm_npcs: list[NpcEntity]
    ) -> StorableDiscussion:
        storable_segments = StorableDiscussion.discussion_to_storable(
            dialogue=discussion.dialogue, realm_npcs=realm_npcs
        )
        return StorableDiscussion(
            realm_id=realm_id,
            timestamp=ts,
            dialogue=storable_segments,
            user_input=user_input,
            input_score=discussion.input_score,
        )

    @classmethod  # type: ignore[misc]
    def from_stored_data(
        cls, discussion: str, user_input: str, input_score: int, realm_id: int, ts: int
    ) -> StorableDiscussion:
        return StorableDiscussion(
            dialogue=json.loads(discussion),
            user_input=user_input,
            input_score=input_score,
            realm_id=realm_id,
            timestamp=ts,
        )

    @classmethod  # type: ignore[misc]
    def discussion_to_storable(
        cls, dialogue: list[DialogueSegment], realm_npcs: list[NpcEntity]
    ) -> list[StoredSegment]:
        name_entity_id_dict = {realm_npc["full_name"]: realm_npc["entity_id"] for realm_npc in realm_npcs}
        return [
            StoredSegment(npc_entity_id=name_entity_id_dict[segment.full_name], segment=segment.dialogue_segment)
            for segment in dialogue
        ]

    @classmethod  # type: ignore[misc]
    def to_string(cls, discussion: StorableDiscussion, realm_npcs: list[NpcEntity]) -> str:
        entity_id_to_name = {realm_npc["entity_id"]: realm_npc["full_name"] for realm_npc in realm_npcs}
        ret = ""
        for segment in discussion["dialogue"]:
            ret += f"{entity_id_to_name[segment['npc_entity_id']]}: {segment['segment']}"
        return ret
