# NPC PARAMS
SEX = ["male", "female"]
ROLE = ["farmer", "miner", "fisherman", "merchant", "trader", "soldier"]
HUNGER = [
    "starving",
    "famished",
    "ravenous",
    "hungry",
    "peckish",
    "content",
    "satisfied",
    "full",
    "stuffed",
    "overfed",
]
HAPPINESS = [
    "miserable",
    "unhappy",
    "slightly content",
    "content",
    "happy",
    "joyful",
    "delighted",
    "ecstatic",
    "blissful",
    "euphoric",
]
BELLIGERENT = [
    "peaceful",
    "calm",
    "slightly agitated",
    "agitated",
    "hostile",
    "combative",
    "antagonistic",
    "belligerent",
    "furious",
    "enraged",
]

AGENT_TEMPLATE = """{name}, a {sex} {role}."""

SUMMARY_EXAMPLE = """Here's the previous conversation that was had in my realm about the event: \"\"\"Summary: "John doubted the artifact's significance, while Mary believed it could heal the village's sick.\"\"\""""
PREVIOUS_SUMMARY_MENTION = (
    """Use the previous conversation's summary (\"\"\"Summary: <summary>\"\"\") to continue the story. """
)

SYSTEM_STRING_TEMPLATE = """Imagine you're the game master for a strategy game, tasked with crafting dialogues for non-player characters (NPCs). Based on a brief character description provided in the format \"\"\"NPCs: <descriptions>\"\"\" and a key event described as \"\"\"event: <event>\"\"\", create engaging dialogues that reflect the NPCs' reactions and perspectives on the event. Ensure each NPC speaks no more than twice and maintain consistency with their character traits. {previous_summary_mention}Introduce a plot twist (such as a love interest, the death of a character, a natural disaster, drama, a magical beast appears) to add depth. Format each dialogue line as "<name>: <phrase>". Conclude with "!end of discussion!". Afterwards, summarize the dialogue, outlining each NPC's contributions and reactions to the event. If unable to generate a conversation, reply with \"\"\"!failure:<enter reason of failure>!\"\"\".

Example:

NPCs: "John, the skeptical blacksmith; Mary, the optimistic healer"
Event: Here is the most interesting event for my realm \"\"\"A mysterious artifact was found in the woods\"\"\"
{summary_example}
Dialogue Start:
John: "I still think it's just an old relic."
Mary: "But imagine the possibilities, John! It could change everything."

!end of discussion!
Summary:
The conversation revolved around the mysterious artifact. John remained skeptical, questioning its value, while Mary was hopeful about its potential healing powers."""

SYSTEM_STRING_HAS_PREV_TOWNHALL = SYSTEM_STRING_TEMPLATE.format(
    previous_summary_mention=PREVIOUS_SUMMARY_MENTION, summary_example=SUMMARY_EXAMPLE
)

SYSTEM_STRING_EMPTY_PREV_TOWNHALL = SYSTEM_STRING_TEMPLATE.format(previous_summary_mention="", summary_example="")

NPCS = """
NPCS:
\"\"\"{npcs}\"\"\".
"""

REALM = """My realm is in the order of {realm_order}."""

EVENT = """Here is the most interesting event for my realm ({realm_name}):
\"\"\"event: {event_string}\"\"\".
"""

PREVIOUS_TOWNHALL = (
    """Here's the previous conversation that was had in my realm about the event: \"\"\"{previous_townhall}\"\"\""""
)

AGENT_CREATION_TEMPLATE = """
    {name}, a {sex} {role}, has just arrived in {realm_name} to settle.
    Upon entering the realm, {name} addresses the lord with the following matters:

    1. Expresses gratitude for the warm welcome and hospitality extended by the realm.
    2. Highlights the skills and contributions he/she brings as a {role}.
    3. Explain his background and where he comes from.
    4. Discusses the significance of recent events: {events}.

    During the speech, {name} maintains a demeanor that is {happiness}, {hunger} and {belligerent}.

    Format the speech like so: <name>:<speech>.
"""
