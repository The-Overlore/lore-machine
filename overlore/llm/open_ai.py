from __future__ import annotations

import logging

from openai import OpenAI

from overlore.eternum.types import Villager
from overlore.llm.constants import (
    EVENT,
    NPCS,
    PREVIOUS_TOWNHALL,
    REALM,
    SYSTEM_STRING_EMPTY_PREV_TOWNHALL,
    SYSTEM_STRING_HAS_PREV_TOWNHALL,
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
        logger.debug("Requesting completion of prompt...")
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
        realm_name: str,
        realm_order: str,
        townhall_summaries: list[str],
        npc_list: list[Villager],
        events: list[StoredEvent],
    ) -> tuple[str, str, str]:
        townhall_summaries_string = "\n".join(townhall_summaries)
        systemPrompt = (
            SYSTEM_STRING_HAS_PREV_TOWNHALL
            if len(townhall_summaries_string) != 0
            else SYSTEM_STRING_EMPTY_PREV_TOWNHALL
        )

        npcs = self.nl_formatter.npcs_to_nl(npc_list)
        event_string = self.nl_formatter.events_to_nl(events)

        userPrompt = REALM.format(realm_name=realm_name, realm_order=realm_order)
        userPrompt += NPCS.format(npcs=npcs)
        userPrompt += EVENT.format(realm_name=realm_name, event_string=event_string)
        userPrompt += (
            PREVIOUS_TOWNHALL.format(previous_townhall=townhall_summaries_string)
            if len(townhall_summaries_string) != 0
            else ""
        )

        return (await self.request_prompt(systemPrompt, userPrompt), systemPrompt, userPrompt)
