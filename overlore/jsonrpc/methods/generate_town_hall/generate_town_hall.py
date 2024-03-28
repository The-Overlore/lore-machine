import json
import logging
from typing import TypedDict, cast

from guardrails import Guard
from jsonrpcserver import Error, InvalidParams, Result, Success, method
from pydantic import BaseModel
from rich import print

from overlore.config import BootConfig, global_config
from overlore.eternum.constants import DAY_IN_SECONDS, Realms
from overlore.graphql.client import ToriiClient
from overlore.jsonrpc.constants import ErrorCodes
from overlore.jsonrpc.methods.generate_town_hall.constant import (
    CURRENT_PLOTLINE_STRING,
    RELEVANT_EVENT_STRING,
    RELEVANT_THOUGHTS_STRING,
    TOWNHALL_SYSTEM_STRING,
    TOWNHALL_USER_STRING,
    USER_INPUT_STRING,
)
from overlore.jsonrpc.methods.generate_town_hall.types import RealmForPrompt
from overlore.llm.client import AsyncOpenAiClient, LlmClient
from overlore.llm.constants import ChatCompletionModel
from overlore.llm.natural_language_formatter import LlmFormatter
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.townhall.request import get_most_important_event, get_npcs_thoughts, store_townhall_information
from overlore.types import DialogueSegment, Townhall
from overlore.utils import get_katana_timestamp

logger = logging.getLogger("overlore")


class MethodParams(BaseModel):
    realm_id: int
    user_input: str
    realm_entity_id: int
    order_id: int


class SuccessResponse(TypedDict):
    townhall_id: int
    dialogue: list[DialogueSegment]


@method
async def generate_town_hall(params: MethodParams) -> Result:
    try:
        MethodParams.model_validate_json(json.dumps(params), strict=True)
    except Exception as e:
        return InvalidParams(str(e))

    logger.info(f"Generating a town hall for realm_entity_id: {params['realm_entity_id']}")
    try:
        return await handle_regular_flow(params=params)
    except RuntimeError as e:
        err = e.args[0]
        return Error(err.value, err.name)


async def handle_regular_flow(params: MethodParams) -> Success:
    guard = Guard.from_pydantic(output_class=Townhall, instructions=TOWNHALL_SYSTEM_STRING, num_reasks=0)
    llm_client = AsyncOpenAiClient()
    torii_client = ToriiClient(torii_url=global_config.env["TORII_GRAPHQL"], events_db=EventsDatabase.instance())
    town_hall_builder = TownHallBuilder(
        llm_client=llm_client, torii_client=torii_client, guard=guard, config=global_config
    )

    townhall_response = await town_hall_builder.build_from_request_params(params=params)

    return Success(json.dumps(townhall_response))


class TownHallBuilder:
    def __init__(self, llm_client: LlmClient, torii_client: ToriiClient, guard: Guard, config: BootConfig):
        self.formater: LlmFormatter = LlmFormatter()
        self.guard = guard
        self.llm_client = llm_client
        self.config = config
        self.torii_client = torii_client

    async def build_from_request_params(self, params: MethodParams) -> SuccessResponse:
        realms = Realms.instance()
        townhall_db = TownhallDatabase.instance()

        realm_id = params["realm_id"]
        realm_entity_id = params["realm_entity_id"]
        realm_name = realms.name_by_id(params["realm_id"])
        user_input = params["user_input"].strip()

        plotline = townhall_db.fetch_plotline_by_realm_id(realm_id=realm_id)

        realm_npcs = await self.torii_client.get_npcs_by_realm_entity_id(realm_entity_id)
        if len(realm_npcs) < 2:
            raise RuntimeError(ErrorCodes.LACK_OF_NPCS)

        last_ts = townhall_db.fetch_last_townhall_ts_by_realm_id(realm_id=realm_id)
        if last_ts + DAY_IN_SECONDS < await get_katana_timestamp(self.config.env["KATANA_URL"]):
            townhall_db.delete_daily_townhall_tracker(realm_id=realm_id)

        most_important_event = await get_most_important_event(realm_id=realm_id, config=self.config)

        npcs_thoughts_on_context = await get_npcs_thoughts(
            realm_npcs=realm_npcs,
            most_important_event=most_important_event,
            embedding_source=plotline,
            nl_formatter=self.formater,
            client=self.llm_client,
            townhall_db=townhall_db,
        )

        prompt_for_llm_call = self.prepare_prompt_for_llm_call(
            realm=RealmForPrompt(
                realm_name=realm_name,
                realm_npcs=realm_npcs,
                most_important_event=most_important_event,
                plotline=plotline,
                npcs_thoughts_on_context=npcs_thoughts_on_context,
                user_input=user_input,
            )
        )

        townhall: Townhall = await self.request_townhall_generation_with_guard(prompt=prompt_for_llm_call)

        row_id = await store_townhall_information(
            townhall=townhall,
            realm_id=realm_id,
            realm_npcs=realm_npcs,
            user_input=user_input,
            plotline=plotline,
            townhall_db=townhall_db,
            llm_client=self.llm_client,
            config=self.config,
        )

        if most_important_event:
            townhall_db.insert_or_update_daily_townhall_tracker(
                realm_id=realm_id, event_row_id=cast(int, most_important_event[0])
            )

        return SuccessResponse(townhall_id=row_id, dialogue=townhall["dialogue"])

    def prepare_prompt_for_llm_call(
        self,
        realm: RealmForPrompt,
    ) -> str:
        relevant_event_string = (
            RELEVANT_EVENT_STRING.format(event_string=self.formater.event_to_nl(realm["most_important_event"]))
            if realm["most_important_event"] is not None
            else ""
        )

        current_plotline_string = (
            CURRENT_PLOTLINE_STRING.format(plotline=realm["plotline"]) if realm["plotline"] else ""
        )

        user_input_string = USER_INPUT_STRING.format(townhall_input=realm["user_input"]) if realm["user_input"] else ""

        (
            RELEVANT_THOUGHTS_STRING.format(thoughts=realm["npcs_thoughts_on_context"])
            if realm["npcs_thoughts_on_context"]
            else ""
        )

        npcs_nl = self.formater.npcs_to_nl(realm["realm_npcs"])

        thoughts_string = RELEVANT_THOUGHTS_STRING.format(thoughts=realm["npcs_thoughts_on_context"])

        prompt = TOWNHALL_USER_STRING.format(
            realm_name=realm["realm_name"],
            relevant_event=relevant_event_string,
            user_input=user_input_string,
            plotline=current_plotline_string,
            thoughts=thoughts_string,
            npcs=npcs_nl,
        )
        return prompt

    async def request_townhall_generation_with_guard(
        self,
        prompt: str,
    ) -> Townhall:
        _, validated_response, *_ = await self.guard(
            llm_api=self.llm_client.request_prompt_completion,
            prompt=prompt,
            model=ChatCompletionModel.GPT_4_PREVIEW.value,
            temperature=1,
        )
        print(self.guard.history.last.tree)

        return cast(Townhall, validated_response)
