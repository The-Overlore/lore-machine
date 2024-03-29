from enum import Enum

# 1 means the two inputs are exactly alike, 0 means they have no similarities
COSINE_SIMILARITY_THRESHOLD = 0.3


class EmbeddingsModel(Enum):
    TEXT_EMBEDDING_SMALL = "text-embedding-3-small"


class ChatCompletionModel(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo-0125"
    GPT_4_PREVIEW = "gpt-4-0125-preview"


GUARD_RAILS_HUB_URL = "https://hty0gc1ok3.execute-api.us-east-1.amazonaws.com/v1/traces"

AGENT_TEMPLATE = """{name} is a {age} year old {sex} {role}. He/she is considered {character_trait}. Realm of origin: {origin_realm}"""

TOWNHALL_SYSTEM = """
Imagine you're the game master for a strategy game, tasked with crafting dialogues for non-player characters (NPCs).
Based on the user's Realm, a brief character description and a key event, create engaging dialogues that reflect the NPCs' reactions and perspectives on the event and/or the Lords' input.
This event might not be an event that happened in the Realm of the user but is nonetheless relevant for it.
If no event is provided, make the NPCs talk about their everyday life.
For combat related events, don't mention the number of damages directly.
The \"Lords\" is the currency of the game.
Create a plot twist such as a love interest, the death of a character, a natural disaster, drama, a magical beast appears.
You must include the plot twist into the conversation to add depth.
${gr.complete_json_suffix_v2}"""

TOWNHALL_USER = (
    """My realm is {realm_name}\n{relevant_event}{townhall_input}{plotline}{thoughts}Here are my NPCs: {npcs}"""
)

RELEVANT_EVENT = "Here is the most interesting event for my realm: {event_string}\n"

CURRENT_PLOTLINE = "This is the current plotline to follow: {plotline}\n"

TOWNHALL_INPUT = "The Lord of the Realm has spoken to its villagers and says: {townhall_input}\n"

RELEVANT_THOUGHTS = "Here are the thoughts of the villagers relevant to the event and plotline: {thoughts}\n"

NPC_PROFILE_SYSTEM = """Imagine you're the game master for a fantasy strategy game, you are tasked with creating a Non-Playable Character.
${gr.complete_json_suffix_v2}"""

NPC_PROFILE_USER = """Generate an NPC with a {trait_type} trait"""

THOUGHTS_SYSTEM = """You are tasked to generate a collection of NPCs' thoughts post-discussion, highlighting their reflective sentiments and emotional responses to the topics covered.

${gr.complete_json_suffix_v2}"""

THOUGHTS_USER = """Generate for each villager his thoughts on the discussion. \"\"\"villagers: {npcs}\"\"\" \"\"\"discussion: {discussion}\"\"\""""


class GenerationError(Enum):
    LACK_OF_NPCS = "Not enough NPCs"
    NPC_ENTITY_ID_NOT_FOUND = "Can't find npc_entity_id from given full_name"
