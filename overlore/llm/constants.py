TRAIT_TYPE = ["positive", "negative"]

AGENT_TEMPLATE = """{name} is a {age} year old {sex} {role}. He/she is {character_trait}"""

SUMMARY_EXAMPLE = """Here's the previous conversation that was had in my realm about the event: \"\"\"Summary: "John doubted the artifact's significance, while Mary believed it could heal the village's sick.\"\"\""""
PREVIOUS_SUMMARY_MENTION = (
    """Use the previous conversation's summary (\"\"\"Summary: <summary>\"\"\") to continue the story. """
)

SYSTEM_STRING_TEMPLATE = """Imagine you're the game master for a strategy game, tasked with crafting dialogues for non-player characters (NPCs). Based on a brief character description provided in the format \"\"\"NPCs: <descriptions>\"\"\" and a key event described as \"\"\"event: <event>\"\"\", create engaging dialogues that reflect the NPCs' reactions and perspectives on the event. For combat related events, don't mention the number of damages directly. Ensure each NPC speaks no more than twice. {previous_summary_mention} Introduce a plot twist (such as a love interest, the death of a character, a natural disaster, drama, a magical beast appears) to add depth. Format each dialogue line as "<name>: <phrase>\n". Do not answer with anything before the dialogue (specifically do not output "Dialogue start"). Conclude with "!end of discussion!". Afterwards, summarize the dialogue, outlining each NPC's contributions and reactions to the event. If unable to generate a conversation, reply only with \"\"\"!failure!:<enter reason of failure>\"\"\".

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
These are my villagers:
\"\"\"{npcs}\"\"\".
"""

REALM = """My realm is in the order of {realm_order}."""

EVENT = """Here is the most interesting event for my realm ({realm_name}):
\"\"\"event: {event_string}\"\"\".
"""

PREVIOUS_TOWNHALL = (
    """Here's the previous conversation that was had in my realm about the event: \"\"\"{previous_townhall}\"\"\""""
)

AGENT_CREATION_SYSTEM_PROMPT_TEMPLATE = """
    Imagine you're the game master for a strategy game, you are tasked with creating Non-Playable Characters. Use these examples as reference: {examples}. Do not change anything from the output format. Don't go over 31 characters for the full name or for the character trait.
"""
AGENT_CREATION_USER_PROMPT_TEMPLATE = """
    Generate for an npc:
    - fullName
    - characterTrait ({trait_type})
    - role ({roles})
    - sex (0 for male or 1 for female)
    - description
"""

AGENT_CREATION_EXAMPLE = """
fullName: Aurora Frost
characterTrait: Resilient
role: 3
sex: 1
description: Aurora has a determined look in her eyes showing hints of the resilience that will define her character. Her fair hair shines like frost in the sunlight, symbolizing her inner strength and ability to weather any challenge that comes her way.

fullName: Oliver Stone
characterTrait: Intelligent
role: 1
sex: 0
description: Oliver has a thoughtful expression on his face, indicating his innate intelligence even at such a young age. His hazel eyes seem to carefully observe his surroundings, hinting at the sharp mind that will develop as he grows. With a head of dark curls that frame his face, Oliver exudes a quiet sense of wisdom and knowledge beyond his years.
"""
