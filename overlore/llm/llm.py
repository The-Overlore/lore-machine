from __future__ import annotations

import logging
import random
from typing import cast

import openai
from guardrails import Guard
from rich import print

from overlore.llm.constants import (
    NPC_PROFILE_SYSTEM,
    NPC_PROFILE_USER,
    PREVIOUS_TOWNHALL,
    RELEVANT_EVENT,
    TOWNHALL_SYSTEM,
    TOWNHALL_USER,
)
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.npcs.constants import TRAIT_TYPE
from overlore.sqlite.types import StoredEvent
from overlore.types import Npc, Townhall

logger = logging.getLogger("overlore")


class Llm:
    nl_formatter: LlmFormatter = LlmFormatter()

    npc_profile_guard: Guard = Guard.from_pydantic(
        output_class=Npc,
        instructions=NPC_PROFILE_SYSTEM,
        num_reasks=2,
    )

    townhall_guard: Guard = Guard.from_pydantic(output_class=Townhall, instructions=TOWNHALL_SYSTEM, num_reasks=0)

    def request_embedding(self, str_input: str) -> list[float]:
        response = openai.embeddings.create(model="text-embedding-3-small", input=str_input, encoding_format="float")
        return response.data[0].embedding

    def generate_townhall_discussion(
        self,
        realm_name: str,
        townhall_summary: str | None,
        npc_list: list[Npc],
        relevant_event: StoredEvent | None,
    ) -> Townhall:
        previous_townhall = PREVIOUS_TOWNHALL.format(summary=townhall_summary) if townhall_summary is not None else ""

        relevant_event_string = (
            RELEVANT_EVENT.format(event_string=self.nl_formatter.event_to_nl(relevant_event))
            if relevant_event is not None
            else ""
        )
        _raw_llm_response, validated_response, *_rest = self.townhall_guard(
            openai.chat.completions.create,
            model="gpt-4-0125-preview",
            temperature=1,
            prompt=TOWNHALL_USER.format(
                realm_name=realm_name,
                relevant_event=relevant_event_string,
                previous_townhall=previous_townhall,
                npcs=self.nl_formatter.npcs_to_nl(npc_list),
            ),
        )

        print(self.townhall_guard.history.last.tree)
        return cast(Townhall, validated_response)

    def generate_npc_profile(self) -> Npc:
        trait_type = TRAIT_TYPE[random.randrange(2)]

        raw_llm_response, validated_response, *rest = self.npc_profile_guard(
            openai.chat.completions.create,
            model="gpt-3.5-turbo-0125",
            temperature=1.6,
            prompt=NPC_PROFILE_USER.format(trait_type=trait_type),
        )
        print(self.npc_profile_guard.history.last.tree)

        return cast(Npc, validated_response)
