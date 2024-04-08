from typing import TypedDict

from overlore.sqlite.types import StoredEvent
from overlore.types import NpcEntity


class RealmForPrompt(TypedDict):
    realm_name: str
    realm_npcs: list[NpcEntity]
    most_important_event: StoredEvent | None
    npcs_thoughts_on_context: list[str]
    user_input: str
