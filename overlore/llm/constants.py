from enum import Enum


class EmbeddingsModel(Enum):
    TEXT_EMBEDDING_SMALL = "text-embedding-3-small"


class ChatCompletionModel(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo-0125"
    GPT_4_PREVIEW = "gpt-4-0125-preview"


GUARD_RAILS_HUB_URL = "https://hty0gc1ok3.execute-api.us-east-1.amazonaws.com/v1/traces"

AGENT_TEMPLATE = """{name} is a {age} year old {sex} {role}. He/she is considered {character_trait}"""

TOWNHALL_SYSTEM = """Imagine you're the game master for a strategy game, tasked with crafting dialogues for non-player characters (NPCs). Based on the user's Realm, a brief character description and a key event, create engaging dialogues that reflect the NPCs' reactions and perspectives on the event. This event might not be an event that happened in the Realm of the user but is nonetheless relevant for it. If no event is provided, make the NPCs talk about their everyday life. If the user specifies a previous discussion that was held regarding the event, continue that discussion. For combat related events, don't mention the number of damages directly. The Lords is the currency of the game. Create a plot twist such as a love interest, the death of a character, a natural disaster, drama, a magical beast appears. You must include the plot twist into the conversation to add depth.
${gr.complete_json_suffix_v2}"""

TOWNHALL_USER = """My realm is {realm_name}{relevant_event}{previous_townhall}Here are my NPCs: {npcs}"""

RELEVANT_EVENT = ". Here is the most interesting event for my realm: {event_string}"

PREVIOUS_TOWNHALL = (
    """. Here's the previous conversation that was had in my realm about the event: \"\"\"Summary: {summary}\"\"\""""
)

NPC_PROFILE_SYSTEM = """Imagine you're the game master for a fantasy strategy game, you are tasked with creating a Non-Playable Character.
${gr.complete_json_suffix_v2}"""

NPC_PROFILE_USER = """Generate an NPC with a {trait_type} trait"""


class GenerationError(Enum):
    LACK_OF_NPCS = "Not enough NPCs"
