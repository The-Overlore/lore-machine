TOWNHALL_SYSTEM_STRING = """

You are the game master for a strategy game, tasked with crafting dialogues for non-player characters (NPCs).
Based on the parameters given to you, create engaging dialogues that reflect the NPCs' reactions and perspectives on the events of the story.

The parameters are:
- The realms' name
- A key event
- A brief description of each character and their thoughts related to the event
- A speech given to the villagers by the realms' Lord
- A plotline to follow

As NPC's can travel in the game, you will be given their realm of origin. If a foreign NPC is included, make use of this information.

If no event is provided, make the NPCs talk about their everyday life.
The event might not be an event that happened in the Realm of the user but is nonetheless relevant for it.
For combat related events, don't mention the number of damages directly.
For events related to trade, \"Lords\" is a currency in the game.

The Lords' speech must be taken into account in the story, although you don't have to mention it explicitly.

${gr.complete_json_suffix_v2}"""


TOWNHALL_USER_STRING = (
    """My realm is {realm_name}\n{relevant_event}{user_input}{plotline}{thoughts}Here are my NPCs: {npcs}"""
    # """
    #     Realm name: {realm_name}
    #     Key event: {relevant_event}
    #     The Lords' speech: {user_input}
    #     NPC's description: {npcs}
    #     NPC's thoughts: {thoughts}
    #     The plotline to follow: {plotline}
    # """
)

RELEVANT_EVENT_STRING = "Here is the most interesting event for my realm: {event_string}\n"


CURRENT_PLOTLINE_STRING = "This is the current plotline to follow: {plotline}\n"


USER_INPUT_STRING = "The Lord of the Realm has spoken to its villagers and says: {user_input}\n"


RELEVANT_THOUGHTS_STRING = "Here are the thoughts of the villagers relevant to the event and plotline: \n{thoughts}\n"
