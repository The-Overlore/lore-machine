from typing import cast

from overlore.config import BootConfig
from overlore.eternum.constants import Realms
from overlore.graphql.query import get_npcs_by_realm_entity_id
from overlore.llm.constants import GenerationError
from overlore.llm.llm import Llm
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


def handle_townhall_request(data: TownhallRequestMsgData, config: BootConfig) -> WsTownhallResponse | WsErrorResponse:
    llm = Llm()
    realms = Realms.instance()
    townhall_db = TownhallDatabase.instance()

    realm_id = int(cast(str, data.get("realm_id")))
    realm_name = realms.name_by_id(realm_id)
    realm_npcs = get_npcs_by_realm_entity_id(config.env["TORII_GRAPHQL"], int(cast(str, data.get("realm_entity_id"))))
    if len(realm_npcs) < 2:
        raise RuntimeError(GenerationError.LACK_OF_NPCS.value)

    townhall_inputq: str = cast(str, data.get("townhall_input")).strip()
    plotline: str = townhall_inputq if townhall_inputq != "" else townhall_db.fetch_plotline_by_realm(realm_id)
    relevant_event = get_relevant_event(realm_id=realm_id, config=config)

    relevant_thoughts = get_npc_thoughts(realm_npcs, relevant_event, plotline, llm, townhall_db)

    townhall = llm.generate_townhall_discussion(realm_name, realm_npcs, relevant_event, plotline, relevant_thoughts)
    row_id = store_townhall_information(townhall, realm_id, realm_npcs, townhall_inputq, plotline, townhall_db, llm)

    return WsTownhallResponse(townhall_id=row_id, dialogue=townhall["dialogue"])  # type: ignore[index]


def get_relevant_event(realm_id: int, config: BootConfig) -> StoredEvent | None:
    events_db = EventsDatabase.instance()
    realms = Realms.instance()

    ts = get_katana_timestamp(config.env["KATANA_URL"])

    return events_db.fetch_most_relevant_event(realms.position_by_id(realm_id), ts)


def convert_dialogue_to_str(dialogue: list[DialogueSegment]) -> str:
    return "\n".join(
        [f"{dialogue_segment['full_name']}: {dialogue_segment['dialogue_segment']}" for dialogue_segment in dialogue]  # type: ignore[index]
    )


def get_npc_thoughts(
    npc_list: list[NpcEntity],
    relevant_event: StoredEvent | None,
    plotline: str | None,
    llm: Llm,
    townhall_db: TownhallDatabase,
) -> list[str]:
    thoughts = []
    query = ""

    if relevant_event is not None:
        query += llm.nl_formatter.event_to_nl(relevant_event)
    if plotline is not None:
        query += plotline
    if query != "":
        query_embedding = llm.request_embedding(query)
        for npc in npc_list:
            # townhall_db.query_nearest_neighbour
            res = townhall_db.query_cosine_similarity(query_embedding, npc["entity_id"])
            if res is not None:
                row_id = res[0]
                similarity = res[1]

                # Arbitrary number, can be tuned accordingly
                if similarity >= 0.3:
                    thoughts.append(npc["full_name"] + ":" + townhall_db.fetch_npc_thought(row_id))

    return thoughts


def get_entity_id_from_name(full_name: str, realm_npcs: list[NpcEntity]) -> int:
    for npc in realm_npcs:
        if full_name == npc["full_name"]:
            return cast(int, npc["entity_id"])
    return 0


def store_townhall_information(
    townhall: Townhall,
    realm_id: int,
    realm_npcs: list[NpcEntity],
    townhall_inputq: str,
    plotline: str,
    townhall_db: TownhallDatabase,
    llm: Llm,
) -> int:
    dialogue: str = convert_dialogue_to_str(townhall["dialogue"])  # type: ignore[index]
    row_id = townhall_db.insert_townhall_discussion(realm_id, dialogue, townhall_inputq)

    for thought in townhall["thoughts"]:  # type: ignore[index]
        thought_embedding = llm.request_embedding(thought["value"])
        npc_entity_id = get_entity_id_from_name(thought["full_name"], realm_npcs)
        if npc_entity_id != 0:
            townhall_db.insert_npc_thought(npc_entity_id, thought["value"], thought_embedding)

    if townhall_inputq != "":
        if plotline == "":
            townhall_db.insert_plotline(realm_id, townhall["plotline"])  # type: ignore[index]
        else:
            townhall_db.update_plotline(realm_id, townhall["plotline"])  # type: ignore[index]

    return row_id
