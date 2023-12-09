from overlore.prompts.prompts import GptInterface
from overlore.townhall.mocks import fetch_events, fetch_users, fetch_villagers
from overlore.townhall.utils import msg_to_json


async def gen_prompt(users, events, villagers):
    gpt_interface = GptInterface.instance()
    gpt_response = await gpt_interface.generateTownHallDiscussion(villagers, events)
    print(gpt_response)
    # Logic to generate prompt based on users, events and villagers presumably in a overlore/prompt directory
    prompt = f"NPCs that all want to overthrow their lord: {users}"
    return prompt


async def gen_townhall(message: str):
    data = msg_to_json(message)
    if data == {}:
        return "invalid msg"
    users = fetch_users(data.get("user"))
    events = fetch_events(data.get("day"))
    villagers = fetch_villagers()
    prompt = await gen_prompt(users, events, villagers)
    # hand prompt to gpt here
    return prompt
