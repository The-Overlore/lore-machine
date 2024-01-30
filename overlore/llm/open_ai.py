from __future__ import annotations

import logging

from openai import OpenAI

from overlore.eternum.constants import Realms
from overlore.eternum.types import Villager
from overlore.llm.constants import (
    EVENTS_EXTENSION,
    PREVIOUS_TOWNHALL_EXTENSION,
    WORLD_SYSTEM_TEMPLATE,
)
from overlore.llm.natural_language_formatter import NaturalLanguageFormatter
from overlore.sqlite.types import StoredEvent

logger = logging.getLogger("overlore")


class OpenAIHandler:
    _instance: OpenAIHandler | None = None
    API_KEY: str | None = None
    TEXT_GEN_URL: str = "https://api.openai.com/v1/chat/completions"
    EMBEDDINGS_URL: str = "https://api.openai.com/v1/embeddings"
    client: OpenAI
    nl_formatter: NaturalLanguageFormatter

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls) -> OpenAIHandler:
        if cls._instance is None:
            logger.debug("Generating OpenAIHandler interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def init(self, open_ai_api_key: str) -> None:
        self.API_KEY = open_ai_api_key
        self.client = OpenAI(api_key=open_ai_api_key)
        self.nl_formatter = NaturalLanguageFormatter()

    async def request_prompt(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if response is None:
            raise RuntimeError("GPT interface could not request a townhall")
        return str(response.choices[0].message.content)

    async def request_embedding(self, str_input: str) -> list[float]:
        response = self.client.embeddings.create(
            model="text-embedding-ada-002", input=str_input, encoding_format="float"
        )
        return response.data[0].embedding

    async def generate_townhall_discussion(
        self,
        realms: Realms,
        realm_id: int,
        townhall_summaries: list[str],
        npc_list: list[Villager],
        events: list[StoredEvent],
    ) -> str:
        realms = Realms.instance()

        realm_name = realms.name_by_id(realm_id)

        npcs = self.nl_formatter.npcs_to_nl(npc_list)

        systemPrompt = WORLD_SYSTEM_TEMPLATE.format(realm_name=realm_name, npcs=npcs)

        events_string = self.nl_formatter.events_to_nl(events)
        if len(events_string) != 0:
            systemPrompt += EVENTS_EXTENSION.format(events_string=events_string)

        townhalls_string = "\n".join(list(townhall_summaries))
        if len(townhalls_string) != 0:
            systemPrompt += PREVIOUS_TOWNHALL_EXTENSION.format(previous_townhalls=townhalls_string)

        userPrompt = ""

        return await self.request_prompt(systemPrompt, userPrompt)
