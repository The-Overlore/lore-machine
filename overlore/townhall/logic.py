from typing import Any

from overlore.eternum.types import ResourceAmounts
from overlore.prompts.prompts import GptInterface
from overlore.townhall.mocks import fetch_events, fetch_users, fetch_villagers, load_mock_gpt_response
from overlore.utils import str_to_json

# A is calculated by setting a max amount of resources, any value equal to or higher than MAX will get attributed a score of 10.
# The linear equation is then a * MAX + 0 = 10. We can derive a easily from there
A_RESOURCES = 10 / 100
# Same as above
A_DAMAGES = 10 / 1000


async def gen_prompt(users: list[Any], events: list[Any], villagers: list[Any]) -> str:
    gpt_interface = GptInterface.instance()
    gpt_response = await gpt_interface.generateTownHallDiscussion(villagers, events)

    # return gpt_response
    print(f"Generated response: {gpt_response}")
    # Logic to generate prompt based on users, events and villagers presumably in a overlore/prompt directory
    prompt = f"NPCs that all want to overthrow their lord: {users}"
    return prompt


async def gen_townhall(message: str, mock: bool) -> str:
    data = str_to_json(message)
    if data == {}:
        return "invalid msg"
    users = fetch_users(data.get("user"))
    events = fetch_events(data.get("day"))
    villagers = fetch_villagers()

    prompt = await load_mock_gpt_response(data.get("day")) if mock else await gen_prompt(users, events, villagers)

    return prompt


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
