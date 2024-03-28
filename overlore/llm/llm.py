from __future__ import annotations

import logging
import random
from typing import cast

import openai
from guardrails import Guard
from rich import print

from overlore.llm.constants import (
    CURRENT_PLOTLINE,
    NPC_PROFILE_SYSTEM,
    NPC_PROFILE_USER,
    RELEVANT_EVENT,
    RELEVANT_THOUGHTS,
    TOWNHALL_SYSTEM,
    TOWNHALL_USER,
    ChatCompletionModel,
    EmbeddingsModel,
)
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.npcs.constants import TRAIT_TYPE
from overlore.sqlite.types import StoredEvent
from overlore.types import NpcEntity, NpcProfile, Townhall

logger = logging.getLogger("overlore")


class Llm:
    nl_formatter: LlmFormatter = LlmFormatter()

    npc_profile_guard: Guard = Guard.from_pydantic(
        output_class=NpcProfile,
        instructions=NPC_PROFILE_SYSTEM,
        num_reasks=2,
    )

    townhall_guard: Guard = Guard.from_pydantic(output_class=Townhall, instructions=TOWNHALL_SYSTEM, num_reasks=1)

    def request_embedding(self, str_input: str) -> list[float]:
        response = openai.embeddings.create(
            model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value, input=str_input, encoding_format="float"
        )
        return response.data[0].embedding

    def generate_townhall_discussion(
        self,
        realm_name: str,
        npcs: list[NpcEntity],
        relevant_event: StoredEvent | None,
        plotline: str | None,
        relevant_thoughts: list[str],
    ) -> Townhall:
        relevant_event_string = (
            RELEVANT_EVENT.format(event_string=self.nl_formatter.event_to_nl(relevant_event))
            if relevant_event is not None
            else ""
        )

        current_plotline_string = CURRENT_PLOTLINE.format(plotline=plotline) if plotline else ""

        thoughts_string = RELEVANT_THOUGHTS.format(thoughts=relevant_thoughts) if relevant_thoughts else ""

        npcs_nl = self.nl_formatter.npcs_to_nl(npcs)

        _raw_llm_response, validated_response, *_rest = self.townhall_guard(
            openai.chat.completions.create,
            model=ChatCompletionModel.GPT_4_PREVIEW.value,
            temperature=1,
            prompt=TOWNHALL_USER.format(
                realm_name=realm_name,
                relevant_event=relevant_event_string,
                plotline=current_plotline_string,
                thoughts=thoughts_string,
                npcs=npcs_nl,
            ),
        )
        print(self.townhall_guard.history.last.tree)
        return cast(Townhall, validated_response)

    def generate_npc_profile(self) -> NpcProfile:
        trait_type = TRAIT_TYPE[random.randrange(2)]

        raw_llm_response, validated_response, *rest = self.npc_profile_guard(
            openai.chat.completions.create,
            model=ChatCompletionModel.GPT_3_5_TURBO.value,
            temperature=1.8,
            prompt=NPC_PROFILE_USER.format(trait_type=trait_type),
        )
        print(self.npc_profile_guard.history.last.tree)

        return cast(NpcProfile, validated_response)
