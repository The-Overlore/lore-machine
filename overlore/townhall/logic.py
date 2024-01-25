from overlore.eternum.constants import Realms
from overlore.eternum.types import ResourceAmounts, Villager
from overlore.llm.open_ai import OpenAIHandler
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.mocks import fetch_villagers, load_mock_gpt_response
from overlore.utils import get_katana_timestamp, str_to_json

# A is calculated by setting a max amount of resources, any value equal to or higher than MAX will get attributed a score of 10.
# The linear equation is then a * MAX + 0 = 10. We can derive a easily from there
A_RESOURCES = 10 / 100
# Same as above
A_DAMAGES = 10 / 1000


def get_townhall_summary(townhall: str) -> tuple[str, str]:
    res = townhall.split("!end of discussion!")
    return (res[0], res[1])


async def handle_townhall_request(message: str, mock: bool) -> str:
    events_db = EventsDatabase.instance()
    vector_db = VectorDatabase.instance()
    gpt_interface = OpenAIHandler.instance()

    data = str_to_json(message)

    realm_id = int(data.get("realm_id"))

    villagers: list[Villager] = fetch_villagers()

    ts = 10000000 if mock else await get_katana_timestamp()
    # get the most relevant events for the realm
    relevant_events = events_db.fetch_most_relevant(events_db.realms.position_by_id(realm_id), ts)

    relevant_events_ids: list[int] = [int(str(event[0])) for event in relevant_events]

    # get the townhalls summaries that the events already generated + the events_ids which haven't generated any events yet
    (summaries, event_ids_prev_unused) = vector_db.get_townhalls_from_events(relevant_events_ids)

    events_prev_unused = [event for event in relevant_events if event[0] in event_ids_prev_unused]

    generated_townhall = (
        await load_mock_gpt_response(0)
        if mock is True
        else await gpt_interface.generate_townhall_discussion(
            Realms.instance(), realm_id, summaries, villagers, events_prev_unused
        )
    )

    (townhall, summary) = get_townhall_summary(generated_townhall)

    if mock is False:
        # embed new discussion
        embedding = await gpt_interface.request_embedding(generated_townhall)

        # insert our new discussion and its vector in our db
        vector_db.insert_townhall_discussion(
            discussion=townhall, summary=summary, realm_id=realm_id, event_ids=relevant_events_ids, embedding=embedding
        )
    return townhall


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
    elif damage == 0 and len(stolen_resources) == 0:
        raise RuntimeError("Unexpected combat outcome: no damage and no stolen resources")
    else:
        # will never happen but mypy needs this to feel secure, and mypy is ourpy
        return 0.0
