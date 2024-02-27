from overlore.eternum.types import Npc
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.llm.open_ai import OpenAIHandler
from overlore.types import NpcSpawnMsgData


async def spawn_npc(_data: NpcSpawnMsgData) -> Npc:
    llm_formatter = LlmFormatter()
    open_ai = OpenAIHandler.instance()
    npc_string = await open_ai.generate_npc_profile()
    npc_profile = llm_formatter.spawn_npc_response_to_profile(npc_string)
    return npc_profile
