from overlore.townhall.mocks import fetch_events, fetch_users


def gen_prompt(users, events):
    # Logic to generate prompt based on users and events, presumably in a overlore/prompt directory
    prompt = f"NPCs that all want to overthrow their lord: {users}"
    return prompt


def gen_townhall():
    users = fetch_users()
    events = fetch_events()
    prompt = gen_prompt(users, events)
    # hand prompt to gpt here
    return prompt
