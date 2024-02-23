# NPC PARAMS
SEX = ["male", "female"]
ROLE = ["farmer", "miner", "fisherman", "merchant", "trader", "soldier"]
TRAIT_TYPE = ["positive", "negative"]

AGENT_TEMPLATE = """{name}, a {sex} {role}."""

SUMMARY_EXAMPLE = """Here's the previous conversation that was had in my realm about the event: \"\"\"Summary: "John doubted the artifact's significance, while Mary believed it could heal the village's sick.\"\"\""""
PREVIOUS_SUMMARY_MENTION = (
    """Use the previous conversation's summary (\"\"\"Summary: <summary>\"\"\") to continue the story. """
)

SYSTEM_STRING_TEMPLATE = """Imagine you're the game master for a strategy game, tasked with crafting dialogues for non-player characters (NPCs). Based on a brief character description provided in the format \"\"\"NPCs: <descriptions>\"\"\" and a key event described as \"\"\"event: <event>\"\"\", create engaging dialogues that reflect the NPCs' reactions and perspectives on the event. Ensure each NPC speaks no more than twice and maintain consistency with their character traits. {previous_summary_mention}Introduce a plot twist (such as a love interest, the death of a character, a natural disaster, drama, a magical beast appears) to add depth. Format each dialogue line as "<name>: <phrase>\n". Do not output anything else in the dialog. Conclude with "!end of discussion!". Afterwards, summarize the dialogue, outlining each NPC's contributions and reactions to the event. If unable to generate a conversation, reply with \"\"\"!failure:<enter reason of failure>!\"\"\".

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

AGENT_CREATION_SYSTEM_PROMPT_TEMPLATE = """
    Imagine you're the game master for a strategy game, you are tasked with creating Non-Playable Characters. Use these examples as reference: {examples}.
"""
AGENT_CREATION_USER_PROMPT_TEMPLATE = """
    Generate for an npc:
    - age (random between 15 and 50)
    - name
    - surname
    - {trait_type} character trait
    - sex (male or female)
    - role ({roles})
"""

AGENT_CREATION_EXAMPLE = """
    \"\"\"
    Age: 15
    Name: Theo
    Surname: Blackwood
    Character Trait: Resourceful
    Sex: Male
    Role: Farmer

    Theo Blackwood is known for his ability to find quick and clever ways to overcome difficulties, often in innovative ways that surprise those around him. His resourcefulness makes him a key player in any situation, especially in challenging or unexpected circumstances.
    \"\"\"

    \"\"\"
    Age: 47
    Name: Elena
    Surname: Marwood
    Character Trait: Perceptive
    Sex: Female
    Role: Soldier

    Elena Marwood is highly observant and has an exceptional ability to notice and interpret subtle details and nuances that others might overlook. This makes her an invaluable ally or a formidable adversary, depending on where one stands.
    \"\"\"
"""
