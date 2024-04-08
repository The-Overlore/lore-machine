import logging
from typing import cast

from overlore.errors import ErrorCodes
from overlore.eternum.constants import Realms
from overlore.llm.client import LlmClient
from overlore.llm.constants import EmbeddingsModel
from overlore.sqlite.errors import CosineSimilarityNotFoundError
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.sqlite.types import StoredEvent
from overlore.types import (
    DialogueSegment,
    DialogueThoughts,
    NpcEntity,
)

logger = logging.getLogger("overlore")


def get_most_important_event(realm_id: int, katana_time: int) -> StoredEvent | None:
    events_db = EventsDatabase.instance()
    townhall_db = TownhallDatabase.instance()
    realms = Realms.instance()

    stored_event_row_ids = townhall_db.fetch_daily_townhall_tracker(realm_id=realm_id)

    return events_db.fetch_most_relevant_event(realms.position_by_id(realm_id), katana_time, stored_event_row_ids)


def convert_dialogue_to_str(dialogue: list[DialogueSegment]) -> str:
    return "\n".join(
        [f"{dialogue_segment['full_name']}: {dialogue_segment['dialogue_segment']}" for dialogue_segment in dialogue]  # type: ignore[index]
    )


async def get_npcs_thoughts(
    realm_npcs: list[NpcEntity],
    user_input: str,
    client: LlmClient,
    townhall_db: TownhallDatabase,
) -> list[str]:
    thoughts = []

    embedding_question = (
        f'Here\'s what your Lord has to say to you and the other villagers: "{user_input}". What do you think about'
        " that?"
    )
    query_embedding = await client.request_embedding(
        input_str=embedding_question, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
    )

    for npc in realm_npcs:
        try:
            results = townhall_db.query_cosine_similarity(query_embedding, npc["entity_id"])
            (row_id, similarity) = results[0]

            logger.info(f"Similarity of vector {similarity}")

            thoughts.append(npc["full_name"] + ": " + townhall_db.fetch_npc_thought_by_row_id(row_id))

        except CosineSimilarityNotFoundError:
            pass
    return thoughts


def get_entity_id_from_name(full_name: str, npcs: list[NpcEntity]) -> int:
    for npc in npcs:
        if full_name == npc["full_name"]:
            return cast(int, npc["entity_id"])
    raise RuntimeError(ErrorCodes.NPC_ENTITY_ID_NOT_FOUND.value)


async def store_thoughts(
    dialogue_thoughts: DialogueThoughts,
    realm_npcs: list[NpcEntity],
    townhall_db: TownhallDatabase,
    llm_client: LlmClient,
) -> None:
    for npc in dialogue_thoughts["npcs"]:
        first_thought = npc["thoughts"][0]
        second_thought = npc["thoughts"][1]

        first_thought_embedding = await llm_client.request_embedding(
            input_str=first_thought, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
        )
        second_thought_embedding = await llm_client.request_embedding(
            input_str=second_thought, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
        )
        try:
            npc_entity_id = get_entity_id_from_name(npc["full_name"], realm_npcs)
            townhall_db.insert_npc_thought(npc_entity_id, first_thought, first_thought_embedding)
            townhall_db.insert_npc_thought(npc_entity_id, second_thought, second_thought_embedding)
        except KeyError:
            logger.exception(f"Failed to find npc_entity_id for npc named {npc['full_name']}")
