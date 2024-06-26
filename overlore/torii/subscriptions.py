import asyncio
import logging
import sys
from enum import Enum
from typing import Any, Callable, Coroutine, cast

import backoff
from backoff._typing import Details
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport

from overlore.config import BootConfig
from overlore.errors import ErrorCodes
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.llm.constants import EmbeddingsModel
from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.torii.constants import EventType
from overlore.torii.parsing import parse_event, parse_npc_spawn_event
from overlore.types import ToriiEmittedEvent

logger = logging.getLogger("overlore")

OnEventCallbackType = Callable[[ToriiEmittedEvent, BootConfig | None], Coroutine[Any, Any, int]]


class Subscriptions(Enum):
    KEY_BASED_SUB_TEMPLATE = """
          subscription {{
                eventEmitted(keys: ["{event_hash}"]) {{
                    id
                    keys
                    data
                    createdAt
                }}
            }}
        """
    ANY_EVENT_EMITTED = """
          subscription {
                eventEmitted {
                    id
                    keys
                    data
                    createdAt
                }
            }
        """
    ORDER_ACCEPTED = KEY_BASED_SUB_TEMPLATE.format(event_hash=EventType.ORDER_ACCEPTED.value)
    COMBAT_OUTCOME = KEY_BASED_SUB_TEMPLATE.format(event_hash=EventType.COMBAT_OUTCOME.value)
    NPC_SPAWNED = KEY_BASED_SUB_TEMPLATE.format(event_hash=EventType.NPC_SPAWNED.value)
    NONE = "None"


def backoff_logging(details: Details) -> None:
    # Retrieve exception type, value, and traceback
    exc_type, exc_value, _ = sys.exc_info()

    # Format the exception information for logging
    if exc_type is not None and exc_value is not None:
        exc_info = f"{exc_type.__name__}: {exc_value}"
    else:
        exc_info = "No exception information"

    # Format the exception information for logging
    logger.warning(
        f'Backing off {details["wait"]} seconds after {details["tries"]} tries calling function'
        f' {details["target"].__name__} with args and kwargs {details["kwargs"]} due to {exc_info}',
    )


async def torii_event_sub(
    session: Client, on_event_callback: OnEventCallbackType, gql_subscription: Subscriptions, config: BootConfig
) -> None:
    logger.debug("subscribing to %s", gql_subscription)
    async for result in session.subscribe(gql(gql_subscription.value)):  # type: ignore[attr-defined]
        try:
            await on_event_callback(result, config)
        except RuntimeError:
            logger.error("Unable to process event %s in %s", result, gql_subscription)


@backoff.on_exception(backoff.expo, Exception, max_time=300, on_backoff=backoff_logging)
async def use_torii_subscription(
    config: BootConfig, callback_and_subs: list[tuple[Subscriptions, OnEventCallbackType]]
) -> None:
    transport = WebsocketsTransport(url=config.env["TORII_WS"])
    client = Client(transport=transport)
    logger.debug("attempting to establish subscription client...")
    async with client as session:
        tasks = [
            asyncio.create_task(torii_event_sub(session, callback, sub, config), name=sub.name)
            for (sub, callback) in callback_and_subs
        ]
        await asyncio.gather(*tasks)


async def process_received_event(event: ToriiEmittedEvent, _: BootConfig | None = None) -> int:
    events_db = EventsDatabase.instance()

    parsed_event = parse_event(event=event["eventEmitted"])
    added_id: int = events_db.insert_event(event=parsed_event)
    return added_id


async def process_received_spawn_npc_event(
    event: ToriiEmittedEvent,
    config: BootConfig | None,
) -> int:
    if config is None:
        raise RuntimeError(ErrorCodes.EXPECTED_CONFIG)
    npc_db = NpcDatabase.instance()
    discussion_db = DiscussionDatabase.instance()
    llm_client = AsyncOpenAiClient()
    katana_ts = await KatanaClient(url=config.env["KATANA_URL"]).get_katana_ts()

    parsed_event = parse_npc_spawn_event(event=event["eventEmitted"])

    npc_entity_id = cast(int, parsed_event["npc_entity_id"])
    realm_entity_id = cast(int, parsed_event["realm_entity_id"])

    row_id = npc_db.insert_npc_backstory(npc_entity_id, realm_entity_id)

    backstory = npc_db.fetch_npc_backstory(npc_entity_id=npc_entity_id)

    embedding = await llm_client.request_embedding(
        backstory.backstory, model=EmbeddingsModel.TEXT_EMBEDDING_SMALL.value
    )

    row_id = discussion_db.insert_npc_thought(
        npc_entity_id=npc_entity_id,
        thought=backstory.backstory,
        poignancy=backstory.poignancy,
        thought_embedding=embedding,
        katana_ts=katana_ts,
    )

    npc_db.delete_npc_profile_by_realm_entity_id(realm_entity_id)

    try:
        npc_db.verify_npc_profile_is_deleted(realm_entity_id)
        logger.info(f"Deleted npc_profile entry for realm_entity_id {realm_entity_id}")
    except KeyError:
        logger.info(f"Failed to delete npc_profile entry for realm_entity_id {realm_entity_id}")

    return row_id


TORII_SUBSCRIPTIONS: list[tuple[Subscriptions, OnEventCallbackType]] = [
    (Subscriptions.COMBAT_OUTCOME, process_received_event),
    (Subscriptions.ORDER_ACCEPTED, process_received_event),
    (Subscriptions.NPC_SPAWNED, process_received_spawn_npc_event),
]
