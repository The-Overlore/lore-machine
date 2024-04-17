import logging

from overlore.errors import ErrorCodes
from overlore.eternum.realms import Realms
from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.types import StoredEvent
from overlore.types import (
    NpcEntity,
)

logger = logging.getLogger("overlore")


def get_most_important_event(realm_id: int, katana_ts: int) -> StoredEvent | None:
    events_db = EventsDatabase.instance()
    discussion_db = DiscussionDatabase.instance()
    realms = Realms.instance()

    stored_event_row_ids = discussion_db.fetch_events_to_ignore_today(realm_id=realm_id)

    return events_db.fetch_most_relevant_event(realms.position_by_id(realm_id), katana_ts, stored_event_row_ids)


def get_entity_id_from_name(full_name: str, npcs: list[NpcEntity]) -> int:
    for npc in npcs:
        if full_name == npc["full_name"]:
            return npc["entity_id"]
    raise RuntimeError(ErrorCodes.NPC_ENTITY_ID_NOT_FOUND.value)
