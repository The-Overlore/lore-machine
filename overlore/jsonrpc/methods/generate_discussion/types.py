from typing import TypedDict

from overlore.types import DialogueSegment


class DialogueSegmentWithNpcEntityId(TypedDict):
    npc_entity_id: int
    dialogue_segment: DialogueSegment
