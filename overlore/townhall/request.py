import logging
from typing import cast

from overlore.config import BootConfig
from overlore.eternum.constants import Realms
from overlore.jsonrpc.constants import ErrorCodes
from overlore.llm.client import AsyncOpenAiClient
from overlore.llm.constants import COSINE_SIMILARITY_THRESHOLD, EmbeddingsModel
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.sqlite.errors import CosineSimilarityNotFoundError
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.sqlite.types import StoredEvent
from overlore.types import (
    DialogueSegment,
    NpcEntity,
    Townhall,
)
from overlore.utils import get_katana_timestamp

logger = logging.getLogger("overlore")


async def get_most_important_event(realm_id: int, config: BootConfig) -> StoredEvent | None:
    events_db = EventsDatabase.instance()
    townhall_db = TownhallDatabase.instance()
    realms = Realms.instance()

    ts = await get_katana_timestamp(config.env["KATANA_URL"])

    stored_event_row_ids = townhall_db.fetch_daily_townhall_tracker(realm_id=realm_id)

    return events_db.fetch_most_relevant_event(realms.position_by_id(realm_id), ts, stored_event_row_ids)


def convert_dialogue_to_str(dialogue: list[DialogueSegment]) -> str:
    return "\n".join(
        [f"{dialogue_segment['full_name']}: {dialogue_segment['dialogue_segment']}" for dialogue_segment in dialogue]  # type: ignore[index]
    )


async def get_npcs_thoughts(
    realm_npcs: list[NpcEntity],
    most_important_event: StoredEvent | None,
    embedding_source: str | None,
    nl_formatter: LlmFormatter,
    client: AsyncOpenAiClient,
    townhall_db: TownhallDatabase,
) -> list[str]:
    thoughts = []

    if most_important_event is not None:
        embedding_source += nl_formatter.event_to_nl(most_important_event)
    if embedding_source != "":
        query_embedding = await client.request_embedding(
            embedding_source, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
        )
        for npc in realm_npcs:
            try:
                row_id, similarity = townhall_db.query_cosine_similarity(query_embedding, npc["entity_id"])
                if similarity >= COSINE_SIMILARITY_THRESHOLD:
                    thoughts.append(npc["full_name"] + ":" + townhall_db.fetch_npc_thought_by_row_id(row_id))

            except CosineSimilarityNotFoundError:
                pass
    return thoughts


def get_entity_id_from_name(full_name: str, npcs: list[NpcEntity]) -> int:
    for npc in npcs:
        if full_name == npc["full_name"]:
            return cast(int, npc["entity_id"])
    raise RuntimeError(ErrorCodes.NPC_ENTITY_ID_NOT_FOUND.value)


async def store_townhall_information(
    townhall: Townhall,
    realm_id: int,
    realm_npcs: list[NpcEntity],
    user_input: str,
    plotline: str,
    townhall_db: TownhallDatabase,
    llm_client: AsyncOpenAiClient,
    config: BootConfig,
) -> int:
    ts = await get_katana_timestamp(config.env["KATANA_URL"])

    dialogue = convert_dialogue_to_str(townhall["dialogue"])  # type: ignore[index]
    row_id = townhall_db.insert_townhall_discussion(realm_id, dialogue, user_input, ts)

    for thought in townhall["thoughts"]:  # type: ignore[index]
        thought_embedding = await llm_client.request_embedding(
            input_str=thought["value"], model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
        )
        try:
            npc_entity_id = get_entity_id_from_name(thought["full_name"], realm_npcs)
            townhall_db.insert_npc_thought(npc_entity_id, thought["value"], thought_embedding)
        except KeyError:
            logger.exception(f"Failed to find npc_entity_id for npc named {thought['full_name']}")

    if user_input == "":
        if plotline == "":
            townhall_db.insert_plotline(realm_id, townhall["plotline"])  # type: ignore[index]
        else:
            townhall_db.update_plotline(realm_id, townhall["plotline"])  # type: ignore[index]

    return row_id
