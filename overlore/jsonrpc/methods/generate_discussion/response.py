from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TypedDict, cast

from openai import BaseModel

from overlore.errors import ErrorCodes
from overlore.eternum.constants import DAY_IN_SECONDS
from overlore.eternum.realms import Realms
from overlore.jsonrpc.methods.generate_discussion.constant import (
    DISCUSSION_SYSTEM_STRING,
    DISCUSSION_USER_STRING,
    THOUGHTS_SYSTEM_STRING,
)
from overlore.jsonrpc.methods.generate_discussion.types import DialogueSegmentWithNpcEntityId
from overlore.jsonrpc.methods.generate_discussion.utils import (
    convert_discussion_to_str,
    get_entity_id_from_name,
    get_most_important_event,
)
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.llm.constants import ChatCompletionModel, EmbeddingsModel
from overlore.llm.guard import AsyncGuard
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.errors import CosineSimilarityNotFoundError
from overlore.torii.client import ToriiClient
from overlore.types import DialogueSegment, DialogueThoughts, Discussion, NpcAndThoughts, NpcEntity, Thought

logger = logging.getLogger("overlore")

create_and_store_thoughts_tasks = set()


class Context(TypedDict):
    discussion_guard: AsyncGuard
    dialogue_thoughts_guard: AsyncGuard
    llm_client: AsyncOpenAiClient
    torii_client: ToriiClient
    katana_client: KatanaClient


class MethodParams(BaseModel):
    realm_id: int
    user_input: str
    realm_entity_id: int
    order_id: int


class SuccessResponse(TypedDict):
    timestamp: int
    dialogue: list[DialogueSegmentWithNpcEntityId]
    input_score: int


class DiscussionBuilder:
    formatter: LlmFormatter
    discussion_db: DiscussionDatabase
    context: Context
    params: MethodParams
    npcs: list[NpcEntity]
    katana_ts: int
    realm_name: str

    @classmethod
    async def create(cls, context: Context, params: MethodParams) -> DiscussionBuilder:
        self = cls.__new__(cls)

        self.formatter = LlmFormatter()
        self.discussion_db = DiscussionDatabase.instance()

        self.context = context
        self.params = params
        self.npcs = await get_npcs(self.context["torii_client"], self.params.realm_entity_id)
        self.katana_ts = await self.context["katana_client"].get_katana_ts()
        self.realm_name = Realms.instance().name_by_id(params.realm_id)

        delete_events_to_ignore_if_necessary(self.params.realm_id, self.katana_ts, self.discussion_db)

        return self

    def __init__(self) -> None:
        raise RuntimeError("Call create() instead")

    async def create_response(self) -> SuccessResponse:
        discussion = await self.create_and_store_discussion()
        self.create_and_store_thoughts(discussion=discussion)
        return self.create_success_response(discussion=discussion)

    async def create_and_store_discussion(self) -> Discussion:
        discussion = await self.create_discussion()
        self.store_discussion(discussion)
        return discussion

    def create_and_store_thoughts(self, discussion: Discussion) -> None:
        dialogue = convert_discussion_to_str(discussion.dialogue)

        task = asyncio.create_task(
            coro=self.thoughts_task(dialogue=dialogue),
            name="thoughts_task",
        )
        create_and_store_thoughts_tasks.add(task)
        task.add_done_callback(create_and_store_thoughts_tasks.discard)

    def create_success_response(self, discussion: Discussion) -> SuccessResponse:
        response_dialogue = [
            DialogueSegmentWithNpcEntityId(
                npc_entity_id=get_entity_id_from_name(full_name=dialogue_segment.full_name, npcs=self.npcs),
                dialogue_segment=cast(DialogueSegment, dialogue_segment.model_dump()),
            )
            for dialogue_segment in discussion.dialogue
        ]
        return SuccessResponse(timestamp=self.katana_ts, dialogue=response_dialogue, input_score=discussion.input_score)

    async def create_discussion(self) -> Discussion:
        prompt = await self.build_prompt()
        discussion_discussion = await self.request_discussion_with_llm_guard(prompt=prompt)
        return discussion_discussion

    async def build_prompt(self) -> str:
        self.most_important_event = get_most_important_event(realm_id=self.params.realm_id, katana_ts=self.katana_ts)

        npcs_thoughts = await self.get_npcs_thoughts()

        prompt_for_llm_call = self.prepare_prompt_for_llm_call(npcs_thoughts=npcs_thoughts)

        return prompt_for_llm_call

    async def get_npcs_thoughts(self) -> list[str]:
        thoughts = []

        embedding_question = (
            f'Here\'s what your Lord has to say to you and the other villagers: "{self.params.user_input}". What do you'
            " think about that?"
        )
        query_embedding = await self.context["llm_client"].request_embedding(
            input_str=embedding_question, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
        )

        for npc in self.npcs:
            try:
                (thought, katana_ts, cosine_similarity, score) = self.discussion_db.get_highest_scoring_thought(
                    query_embedding=query_embedding, npc_entity_id=npc["entity_id"], katana_ts=self.katana_ts
                )

                logger.info(f"Thought retrieved with a score of {score} (cos_sim: {cosine_similarity}) -> {thought}")

                date_time = datetime.fromtimestamp(katana_ts)

                thoughts.append(f"Thought was had on {date_time} - {npc['full_name']} : {thought}")

            except CosineSimilarityNotFoundError as e:
                logger.error(
                    f"Failure to fetch thoughts. NPC entity id: {npc['entity_id']}. Embedding question"
                    f" {embedding_question}. Katana ts {self.katana_ts}"
                )
                raise RuntimeError(ErrorCodes.NO_THOUGHT_FOUND) from e
        return thoughts

    def store_discussion(self, discussion: Discussion) -> None:
        dialogue = convert_discussion_to_str(discussion.dialogue)

        self.discussion_db.insert_discussion(
            realm_id=self.params.realm_id,
            discussion=dialogue,
            user_input=self.params.user_input,
            input_score=discussion.input_score,
            ts=self.katana_ts,
        )

        if self.most_important_event:
            self.discussion_db.insert_or_update_events_to_ignore_today(
                katana_ts=self.katana_ts,
                realm_id=self.params.realm_id,
                event_id=cast(int, self.most_important_event[0]),
            )

    async def thoughts_task(self, dialogue: str) -> None:
        thoughts: DialogueThoughts = await self.request_thoughts_with_guard(prompt=dialogue)
        await self.store_thoughts(thoughts=thoughts)

    async def store_thoughts(
        self,
        thoughts: DialogueThoughts,
    ) -> None:
        for npc_and_thoughts in thoughts.npcs:
            await self.store_thoughts_per_npc(npc_and_thoughts=npc_and_thoughts)

    async def store_thoughts_per_npc(self, npc_and_thoughts: NpcAndThoughts) -> None:
        npc_entity_id = get_entity_id_from_name(npc_and_thoughts.full_name, self.npcs)

        first_thought = npc_and_thoughts.thoughts[0]
        second_thought = npc_and_thoughts.thoughts[1]

        await self.embed_and_store_thought_and_embedding(thought=first_thought, npc_entity_id=npc_entity_id)
        await self.embed_and_store_thought_and_embedding(thought=second_thought, npc_entity_id=npc_entity_id)

    async def embed_and_store_thought_and_embedding(self, thought: Thought, npc_entity_id: int) -> None:
        thought_str = f"Thought created during a conversation in {self.realm_name} - {thought.thought}"
        embedding = await self.context["llm_client"].request_embedding(
            input_str=thought_str, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
        )
        self.discussion_db.insert_npc_thought(
            npc_entity_id=npc_entity_id,
            thought=thought_str,
            poignancy=thought.poignancy,
            katana_ts=self.katana_ts,
            thought_embedding=embedding,
        )

    def prepare_prompt_for_llm_call(self, npcs_thoughts: list[str]) -> str:
        event_string = ""
        if self.most_important_event is not None:
            event_string = self.formatter.event_to_nl(self.most_important_event)

        npc_memories = "\n".join(npcs_thoughts)

        npcs_nl = self.formatter.npcs_to_nl(self.npcs)

        date_time = datetime.fromtimestamp(self.katana_ts)

        prompt = DISCUSSION_USER_STRING.format(
            date_time=date_time,
            realm_name=self.realm_name,
            relevant_event=event_string,
            user_input=self.params.user_input,
            npc_memories=npc_memories,
            npcs=npcs_nl,
        )
        return prompt

    async def request_discussion_with_llm_guard(
        self,
        prompt: str,
    ) -> Discussion:
        response = await self.context["discussion_guard"].call_llm_with_guard(
            api_function=self.context["llm_client"].request_prompt_completion,
            instructions=DISCUSSION_SYSTEM_STRING,
            prompt=prompt,
            model=ChatCompletionModel.GPT_4_PREVIEW.value,
            temperature=1,
        )
        return response  # type: ignore[no-any-return]

    async def request_thoughts_with_guard(
        self,
        prompt: str,
    ) -> DialogueThoughts:
        response = await self.context["dialogue_thoughts_guard"].call_llm_with_guard(
            api_function=self.context["llm_client"].request_prompt_completion,
            instructions=THOUGHTS_SYSTEM_STRING,
            prompt=prompt,
            model=ChatCompletionModel.GPT_3_5_TURBO.value,
            temperature=1,
        )

        return response  # type: ignore[no-any-return]


async def get_npcs(torii_client: ToriiClient, realm_entity_id: int) -> list[NpcEntity]:
    realm_npcs = await torii_client.get_npcs_by_realm_entity_id(realm_entity_id)
    if len(realm_npcs) < 2:
        raise RuntimeError(ErrorCodes.LACK_OF_NPCS)

    return realm_npcs


def delete_events_to_ignore_if_necessary(realm_id: int, katana_ts: int, discussion_db: DiscussionDatabase) -> None:
    ts_of_last_generated_towhall = discussion_db.fetch_last_discussion_ts_by_realm_id(realm_id=realm_id)
    if ts_of_last_generated_towhall + DAY_IN_SECONDS < katana_ts:
        discussion_db.delete_events_to_ignore_today(realm_id=realm_id)
