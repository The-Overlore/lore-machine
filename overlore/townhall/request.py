import logging
from typing import cast

from overlore.config import BootConfig
from overlore.eternum.constants import DAY_IN_SECONDS, Realms
from overlore.graphql.query import get_npcs_by_realm_entity_id
from overlore.llm.constants import COSINE_SIMILARITY_THRESHOLD, GenerationError
from overlore.llm.llm import Llm
from overlore.sqlite.errors import CosineSimilarityNotFoundError
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.sqlite.types import StoredEvent
from overlore.types import (
    DialogueSegment,
    NpcEntity,
    Townhall,
    TownhallRequestMsgData,
    WsErrorResponse,
    WsTownhallResponse,
)
from overlore.utils import get_katana_timestamp

logger = logging.getLogger("overlore")


def handle_townhall_request(data: TownhallRequestMsgData, config: BootConfig) -> WsTownhallResponse | WsErrorResponse:
    llm = Llm()
    realms = Realms.instance()
    townhall_db = TownhallDatabase.instance()

    realm_id = int(cast(str, data.get("realm_id")))
    realm_entity_id = int(cast(str, data.get("realm_entity_id")))
    townhall_input = cast(str, data.get("townhall_input")).strip()

    realm_name = realms.name_by_id(i=realm_id)
    plotline = townhall_db.fetch_plotline_by_realm_id(realm_id=realm_id)

    npcs = get_npcs_by_realm_entity_id(torii_endpoint=config.env["TORII_GRAPHQL"], realm_entity_id=realm_entity_id)
    if len(npcs) < 2:
        raise RuntimeError(GenerationError.LACK_OF_NPCS.value)

    last_ts = townhall_db.fetch_last_townhall_ts_by_realm_id(realm_id=realm_id)
    if last_ts + DAY_IN_SECONDS < get_katana_timestamp(config.env["KATANA_URL"]):
        townhall_db.delete_daily_townhall_tracker(realm_id=realm_id)

    relevant_event = get_relevant_event(realm_id=realm_id, config=config)

    if relevant_event:
        townhall_db.insert_or_update_daily_townhall_tracker(
            realm_id=realm_id, event_row_id=cast(int, relevant_event[0])
        )

    relevant_thoughts = get_npc_thoughts(npcs=npcs, event=relevant_event, plotline=plotline)

    townhall = llm.generate_townhall_discussion(
        realm_name=realm_name,
        npcs=npcs,
        relevant_event=relevant_event,
        plotline=plotline,
        relevant_thoughts=relevant_thoughts,
    )

    row_id = store_townhall_information(
        townhall=townhall, realm_id=realm_id, npcs=npcs, townhall_input=townhall_input, plotline=plotline, config=config
    )

    return WsTownhallResponse(townhall_id=row_id, dialogue=townhall["dialogue"])  # type: ignore[index]


def get_relevant_event(realm_id: int, config: BootConfig) -> StoredEvent | None:
    events_db = EventsDatabase.instance()
    townhall_db = TownhallDatabase.instance()
    realms = Realms.instance()

    ts = get_katana_timestamp(config.env["KATANA_URL"])

    stored_event_row_ids = townhall_db.fetch_daily_townhall_tracker(realm_id=realm_id)

    return events_db.fetch_most_relevant_event(realms.position_by_id(realm_id), ts, stored_event_row_ids)


def convert_dialogue_to_str(dialogue: list[DialogueSegment]) -> str:
    return "\n".join(
        [f"{dialogue_segment['full_name']}: {dialogue_segment['dialogue_segment']}" for dialogue_segment in dialogue]  # type: ignore[index]
    )


def get_npc_thoughts(
    npcs: list[NpcEntity],
    event: StoredEvent | None,
    plotline: str,
) -> list[str]:
    townhall_db = TownhallDatabase.instance()
    llm = Llm()

    thoughts = []
    embedding_source = plotline

    if event is not None:
        embedding_source += llm.nl_formatter.event_to_nl(event)

    if embedding_source != "":
        query_embedding = llm.request_embedding(embedding_source)

        for npc in npcs:
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
    raise RuntimeError(GenerationError.NPC_ENTITY_ID_NOT_FOUND.value)


def store_townhall_information(
    townhall: Townhall, realm_id: int, npcs: list[NpcEntity], townhall_input: str, plotline: str, config: BootConfig
) -> int:
    townhall_db = TownhallDatabase.instance()
    llm = Llm()

    ts = get_katana_timestamp(config.env["KATANA_URL"])

    dialogue = convert_dialogue_to_str(townhall["dialogue"])  # type: ignore[index]
    row_id = townhall_db.insert_townhall_discussion(realm_id, dialogue, townhall_input, ts)

    for thought in townhall["thoughts"]:  # type: ignore[index]
        thought_embedding = llm.request_embedding(thought["value"])

        try:
            npc_entity_id = get_entity_id_from_name(thought["full_name"], npcs)
            townhall_db.insert_npc_thought(npc_entity_id, thought["value"], thought_embedding)
        except KeyError:
            logger.exception(f"Failed to find npc_entity_id for npc named {thought['full_name']}")

    if townhall_input == "":
        if plotline == "":
            townhall_db.insert_plotline(realm_id, townhall["plotline"])  # type: ignore[index]
        else:
            townhall_db.update_plotline(realm_id, townhall["plotline"])  # type: ignore[index]

    return row_id
