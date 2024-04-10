import asyncio
import logging
from typing import TypedDict, cast

from openai import BaseModel

from overlore.errors import ErrorCodes
from overlore.eternum.constants import DAY_IN_SECONDS, Realms
from overlore.jsonrpc.methods.generate_town_hall.constant import (
    THOUGHTS_SYSTEM_STRING,
    TOWNHALL_SYSTEM_STRING,
    TOWNHALL_USER_STRING,
)
from overlore.jsonrpc.methods.generate_town_hall.types import RealmForPrompt
from overlore.jsonrpc.methods.generate_town_hall.utils import (
    convert_dialogue_to_str,
    get_most_important_event,
    get_npcs_thoughts,
    store_thoughts,
)
from overlore.katana.client import KatanaClient
from overlore.llm.client import LlmClient
from overlore.llm.constants import ChatCompletionModel
from overlore.llm.guard import AsyncGuard
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.torii.client import ToriiClient
from overlore.types import DialogueSegment, DialogueThoughts, NpcEntity, Townhall

logger = logging.getLogger("overlore")

generate_and_store_thoughts_tasks = set()


class MethodParams(BaseModel):
    realm_id: int
    user_input: str
    realm_entity_id: int
    order_id: int


class SuccessResponse(TypedDict):
    townhall_id: int
    dialogue: list[DialogueSegment]


class TownHallBuilder:
    def __init__(
        self,
        llm_client: LlmClient,
        torii_client: ToriiClient,
        katana_client: KatanaClient,
        town_hall_guard: AsyncGuard,
        dialogue_thoughts_guard: AsyncGuard,
    ):
        self.formater: LlmFormatter = LlmFormatter()
        self.llm_client = llm_client
        self.torii_client = torii_client
        self.katana_client = katana_client
        self.town_hall_guard = town_hall_guard
        self.dialogue_thoughts_guard = dialogue_thoughts_guard

    async def build_from_request_params(self, params: MethodParams) -> SuccessResponse:
        townhall_db = TownhallDatabase.instance()

        realm_id = params["realm_id"]  # type: ignore[index]
        realm_entity_id = params["realm_entity_id"]  # type: ignore[index]
        realm_name = Realms.instance().name_by_id(params["realm_id"])  # type: ignore[index]
        user_input = params["user_input"].strip()  # type: ignore[index]

        realm_npcs = await self.torii_client.get_npcs_by_realm_entity_id(realm_entity_id)
        if len(realm_npcs) < 2:
            raise RuntimeError(ErrorCodes.LACK_OF_NPCS)

        katana_time = await self.katana_client.get_katana_timestamp()

        last_ts = townhall_db.fetch_last_townhall_ts_by_realm_id(realm_id=realm_id)
        if last_ts + DAY_IN_SECONDS < katana_time:
            townhall_db.delete_daily_townhall_tracker(realm_id=realm_id)

        most_important_event = get_most_important_event(realm_id=realm_id, katana_time=katana_time)

        npcs_thoughts_on_context = await get_npcs_thoughts(
            realm_npcs=realm_npcs,
            user_input=user_input,
            client=self.llm_client,
            townhall_db=townhall_db,
        )

        prompt_for_llm_call = self.prepare_prompt_for_llm_call(
            realm=RealmForPrompt(
                realm_name=realm_name,
                realm_npcs=realm_npcs,
                most_important_event=most_important_event,
                npcs_thoughts_on_context=npcs_thoughts_on_context,
                user_input=user_input,
            )
        )

        townhall: Townhall = await self.request_town_hall_with_guard(
            prompt=prompt_for_llm_call,
        )

        dialogue = convert_dialogue_to_str(townhall.dialogue)
        row_id = townhall_db.insert_townhall_discussion(realm_id, dialogue, user_input, katana_time)

        task = asyncio.create_task(
            coro=self.generate_and_store_thoughts(dialogue=dialogue, realm_name=realm_name, realm_npcs=realm_npcs),
            name="generate_and_store_thoughts",
        )

        generate_and_store_thoughts_tasks.add(task)
        task.add_done_callback(generate_and_store_thoughts_tasks.discard)
        print(generate_and_store_thoughts_tasks)

        if most_important_event:
            townhall_db.insert_or_update_daily_townhall_tracker(
                realm_id=realm_id, event_row_id=cast(int, most_important_event[0])
            )

        return SuccessResponse(
            townhall_id=row_id,
            dialogue=[cast(DialogueSegment, dialogue_segment.model_dump()) for dialogue_segment in townhall.dialogue],
        )

    async def generate_and_store_thoughts(self, dialogue: str, realm_name: str, realm_npcs: list[NpcEntity]) -> None:
        dialogue_thoughts: DialogueThoughts = await self.request_thoughts_with_guard(prompt=dialogue)

        await store_thoughts(
            realm_name=realm_name,
            dialogue_thoughts=dialogue_thoughts,
            realm_npcs=realm_npcs,
            llm_client=self.llm_client,
        )

    def prepare_prompt_for_llm_call(
        self,
        realm: RealmForPrompt,
    ) -> str:
        event_string = ""
        if realm["most_important_event"] is not None:
            event_string = self.formater.event_to_nl(realm["most_important_event"])

        npc_memories = "\n".join(realm["npcs_thoughts_on_context"])

        npcs_nl = self.formater.npcs_to_nl(realm["realm_npcs"])

        prompt = TOWNHALL_USER_STRING.format(
            realm_name=realm["realm_name"],
            relevant_event=event_string,
            user_input=realm["user_input"],
            npc_memories=npc_memories,
            npcs=npcs_nl,
        )
        return prompt

    async def request_town_hall_with_guard(
        self,
        prompt: str,
    ) -> Townhall:
        response = await self.town_hall_guard.call_llm_with_guard(
            api_function=self.llm_client.request_prompt_completion,
            instructions=TOWNHALL_SYSTEM_STRING,
            prompt=prompt,
            model=ChatCompletionModel.GPT_4_PREVIEW.value,
            temperature=1.2,
        )
        return response  # type: ignore[no-any-return]

    async def request_thoughts_with_guard(
        self,
        prompt: str,
    ) -> DialogueThoughts:
        response = await self.dialogue_thoughts_guard.call_llm_with_guard(
            api_function=self.llm_client.request_prompt_completion,
            instructions=THOUGHTS_SYSTEM_STRING,
            prompt=prompt,
            model=ChatCompletionModel.GPT_3_5_TURBO.value,
            temperature=1,
        )

        return response  # type: ignore[no-any-return]
