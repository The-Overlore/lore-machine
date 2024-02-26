from typing import cast

from overlore.config import BootConfig
from overlore.eternum.constants import Realms
from overlore.eternum.types import Npc, ResourceAmounts
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.types import StoredEvent
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.mocks import MOCK_VILLAGERS
from overlore.utils import get_katana_timestamp, str_to_json

# A is calculated by setting a max amount of resources, any value equal to or higher than MAX will get attributed a score of 10.
# The linear equation is then a * MAX + 0 = 10. We can derive a easily from there
A_RESOURCES = 10 / 100
# Same as above
A_DAMAGES = 10 / 1000

MOCK_GPT_RESPONSE = (
    "Paul: Hello World\nNancy:Yes, Hello World indeed!!end of discussion! Villagers say hello",
    "mock system prompt",
    "mock user prompt",
)


def is_error(townhall: str) -> bool:
    return townhall.find("!failure!") != -1


def get_townhall_summary(townhall: str) -> tuple[str, str]:
    res = townhall.split("!end of discussion!")
    return (res[0], res[1])


async def handle_townhall_request(message: str, config: BootConfig) -> tuple[int, str, str, str]:
    events_db = EventsDatabase.instance()
    vector_db = VectorDatabase.instance()
    gpt_interface = OpenAIHandler.instance()
    realms = Realms.instance()

    try:
        data = str_to_json(message)
    except Exception as error:
        return (0, f"Failure to generate a dialog: {error}", "", "")

    realm_id = int(data.get("realm_id"))
    realm_name = realms.name_by_id(realm_id)

    realm_order_id = int(data.get("orderId"))
    realm_order = realms.order_by_order_id(realm_order_id)

    npcs: list[Npc] = data.get("npcs")

    # This is only temporary until the NPCs actually age. Otherwise for now we get the same npc 5 times
    npcs = cast(list[Npc], MOCK_VILLAGERS)

    ts = await get_katana_timestamp(config.env["KATANA_URL"])

    # get the most relevant events for the realm
    relevant_events: list[StoredEvent] = events_db.fetch_most_relevant(events_db.realms.position_by_id(realm_id), ts)

    relevant_events_ids: list[int] = [int(str(event[0])) for event in relevant_events]

    # get the townhalls summaries that the events already generated + the events_ids which haven't generated any events yet
    (summaries, event_ids_prev_unused) = vector_db.get_townhalls_from_events(relevant_events_ids)

    [event for event in relevant_events if event[0] in event_ids_prev_unused]

    # TODO: find a way to mock the ChatGPT response with the responses library instead of loading from file. Then we can avoid having to do this check which isn't really elegant (https://github.com/The-Overlore/lore-machine/issues/67)
    (generated_townhall, systemPrompt, userPrompt) = (
        MOCK_GPT_RESPONSE
        if config.mock is True
        else await gpt_interface.generate_townhall_discussion(realm_name, realm_order, summaries, npcs, relevant_events)
    )

    if is_error(generated_townhall):
        return (0, f"Failure to generate a dialog: {generated_townhall}", "", "")

    (townhall, summary) = get_townhall_summary(generated_townhall)

    row_id = 0

    if config.mock is False:
        # embed new discussion
        embedding = await gpt_interface.request_embedding(generated_townhall)
        # insert our new discussion and its vector in our db
        row_id = vector_db.insert_townhall_discussion(
            discussion=townhall, summary=summary, realm_id=realm_id, event_ids=relevant_events_ids, embedding=embedding
        )

    return (row_id, townhall, systemPrompt, userPrompt)


def get_importance_from_resources(resources: ResourceAmounts) -> float:
    """
    Takes the total amount of resources traded and assigns a score based on the following linear equation: A_RESOURCES * total_resources_amount
    The slope of A is ascending, the more resources, the higher the score
    """
    total_resources_amount = sum([resource["amount"] for resource in resources])
    return 10.0 if total_resources_amount > 100 else A_RESOURCES * total_resources_amount


def get_trade_importance(resources: ResourceAmounts) -> float:
    return get_importance_from_resources(resources)


def get_combat_outcome_importance(stolen_resources: ResourceAmounts, damage: int) -> float:
    """
    Checks if we stole resources or if someone suffered damages (one can't happen if the other is true).
        - If damages the score will be A_DAMAGES * damage
        - If resources the score will be calculated by get_importance_from_resources
    """
    if damage > 0 and len(stolen_resources) == 0:
        return 10.0 if damage > 1000 else A_DAMAGES * damage
    elif damage == 0 and len(stolen_resources) > 0:
        return get_importance_from_resources(resources=stolen_resources)
    elif damage > 0 and len(stolen_resources) > 0:
        raise RuntimeError("Unexpected combat outcome: both damage and stolen resources are set")
    else:
        # will never happen but mypy needs this to feel secure, and mypy is ourpy
        return 0.0
