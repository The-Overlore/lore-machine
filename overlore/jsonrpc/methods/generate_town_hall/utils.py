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


def get_most_important_event(realm_id: int, katana_ts: int) -> StoredEvent | None:
    events_db = EventsDatabase.instance()
    townhall_db = TownhallDatabase.instance()
    realms = Realms.instance()

    stored_event_row_ids = townhall_db.fetch_daily_townhall_tracker(realm_id=realm_id)

    return events_db.fetch_most_relevant_event(realms.position_by_id(realm_id), katana_ts, stored_event_row_ids)


def convert_dialogue_to_str(dialogue: list[DialogueSegment]) -> str:
    return "\n".join(
        [f"{dialogue_segment.full_name}: {dialogue_segment.dialogue_segment}" for dialogue_segment in dialogue]
    )


async def get_npcs_thoughts(
    realm_npcs: list[NpcEntity],
    user_input: str,
    katana_ts: int,
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
            (thought, cosine_similarity, score) = townhall_db.get_highest_scoring_thought(
                query_embedding=query_embedding, npc_entity_id=npc["entity_id"], katana_ts=katana_ts
            )

            logger.info(f"Thought retrieved with a score of {score} (cos_sim: {cosine_similarity}) -> {thought}")

            thoughts.append(npc["full_name"] + ": " + thought)

        except CosineSimilarityNotFoundError:
            pass
    return thoughts


def get_entity_id_from_name(full_name: str, npcs: list[NpcEntity]) -> int:
    for npc in npcs:
        if full_name == npc["full_name"]:
            return cast(int, npc["entity_id"])
    raise RuntimeError(ErrorCodes.NPC_ENTITY_ID_NOT_FOUND.value)


async def store_thoughts(
    realm_name: str,
    dialogue_thoughts: DialogueThoughts,
    realm_npcs: list[NpcEntity],
    llm_client: LlmClient,
    katana_ts: int,
) -> None:
    townhall_db = TownhallDatabase.instance()

    for npc in dialogue_thoughts.npcs:
        thought_0 = npc.thoughts[0]
        thought_1 = npc.thoughts[1]

        first_thought = f"Thought created during a conversation in {realm_name} - {thought_0.thought}"
        second_thought = f"Thought created during a conversation in {realm_name} - {thought_1.thought}"

        first_thought_embedding = await llm_client.request_embedding(
            input_str=first_thought, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
        )
        second_thought_embedding = await llm_client.request_embedding(
            input_str=second_thought, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
        )
        try:
            npc_entity_id = get_entity_id_from_name(npc.full_name, realm_npcs)
            townhall_db.insert_npc_thought(
                npc_entity_id=npc_entity_id,
                thought=first_thought,
                poignancy=thought_0.poignancy,
                katana_ts=katana_ts,
                thought_embedding=first_thought_embedding,
            )
            townhall_db.insert_npc_thought(
                npc_entity_id=npc_entity_id,
                thought=second_thought,
                poignancy=thought_1.poignancy,
                katana_ts=katana_ts,
                thought_embedding=second_thought_embedding,
            )
        except KeyError:
            logger.exception(f"Failed to find npc_entity_id for npc named {npc.full_name}")
