from typing import cast

from overlore.config import BootConfig
from overlore.eternum.constants import Realms
from overlore.llm.constants import GenerationError
from overlore.llm.llm import Llm
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.types import StoredEvent
from overlore.sqlite.vector_db import VectorDatabase
from overlore.types import DialogueSegment, Npc, TownhallRequestMsgData, WsErrorResponse, WsTownhallResponse
from overlore.utils import get_katana_timestamp


def handle_townhall_request(data: TownhallRequestMsgData, config: BootConfig) -> WsTownhallResponse | WsErrorResponse:
    vector_db = VectorDatabase.instance()
    llm = Llm()
    realms = Realms.instance()

    realm_id = int(cast(str, data.get("realm_id")))
    realm_npcs: list[Npc] = cast(list[Npc], data.get("npcs"))
    realm_name = realms.name_by_id(realm_id)

    if len(realm_npcs) < 2:
        raise RuntimeError(GenerationError.LACK_OF_NPCS.value)

    (relevant_event_id, relevant_event, summary) = get_event_and_summary(
        realm_id=realm_id, vector_db=vector_db, config=config
    )

    townhall = llm.generate_townhall_discussion(realm_name, summary, realm_npcs, relevant_event)

    dialogue: str = convert_dialogue_to_str(townhall["dialogue"])  # type: ignore[index]

    # embed new discussion
    embedding = llm.request_embedding(dialogue)

    # insert our new discussion and its vector in our db
    row_id = vector_db.insert_townhall_discussion(
        discussion=dialogue,
        summary=townhall["summary"],  # type: ignore[index]
        realm_id=realm_id,
        event_id=relevant_event_id,
        embedding=embedding,
    )

    return WsTownhallResponse(townhall_id=row_id, dialogue=townhall["dialogue"])  # type: ignore[index]


def get_event_and_summary(
    realm_id: int, vector_db: VectorDatabase, config: BootConfig
) -> tuple[int, StoredEvent | None, str | None]:
    events_db = EventsDatabase.instance()
    realms = Realms.instance()

    ts = get_katana_timestamp(config.env["KATANA_URL"])

    relevant_event: StoredEvent | None = events_db.fetch_most_relevant_event(realms.position_by_id(realm_id), ts)

    if relevant_event is None:
        return (0, None, None)

    relevant_event_id: int = cast(int, relevant_event[0])

    summary = vector_db.get_townhall_from_event(relevant_event_id, realm_id=realm_id)

    return (relevant_event_id, relevant_event, summary)


def convert_dialogue_to_str(dialogue: list[DialogueSegment]) -> str:
    return "\n".join(
        [f"{dialogue_segment['full_name']}: {dialogue_segment['dialogue_segment']}" for dialogue_segment in dialogue]  # type: ignore[index]
    )
