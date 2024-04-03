TOWNHALL_SYSTEM_STRING = """
Imagine you're the game master for a strategy game, tasked with crafting dialogues for non-player characters (NPCs).
Based on the user's Realm, a brief character description and a key event, create engaging dialogues that reflect the NPCs' reactions and perspectives on the event and/or the Lords' input.
This event might not be an event that happened in the Realm of the user but is nonetheless relevant for it.
If no event is provided, make the NPCs talk about their everyday life.
For combat related events, don't mention the number of damages directly.
The \"Lords\" is the currency of the game.
Create a plot twist such as a love interest, the death of a character, a natural disaster, drama, a magical beast appears.
You must include the plot twist into the conversation to add depth.
${gr.complete_json_suffix_v2}"""

TOWNHALL_USER_STRING = (
    """My realm is {realm_name}\n{relevant_event}{user_input}{plotline}{thoughts}Here are my NPCs: {npcs}"""
)

RELEVANT_EVENT_STRING = "Here is the most interesting event for my realm: {event_string}\n"

CURRENT_PLOTLINE_STRING = "This is the current plotline to follow: {plotline}\n"

USER_INPUT_STRING = "The Lord of the Realm has spoken to its villagers and says: {user_input}\n"

RELEVANT_THOUGHTS_STRING = "Here are the thoughts of the villagers relevant to the event and plotline: {thoughts}\n"
