import asyncio
import functools
import json
import logging
import os
import signal
from types import FrameType
from typing import cast

import responses
from websockets import serve
from websockets.exceptions import ConnectionClosedError

from overlore.config import BootConfig
from overlore.graphql.boot_sync import torii_boot_sync
from overlore.graphql.subscriptions import (
    OnEventCallbackType,
    Subscriptions,
    delete_npc_from_db,
    process_received_event,
    use_torii_subscription,
)
from overlore.llm.constants import GUARD_RAILS_HUB_URL
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.townhall.mocks import MOCK_KATANA_RESPONSE, MOCK_VILLAGERS, with_mock_responses
from overlore.townhall.request import handle_townhall_request
from overlore.types import WsTownhallResponse
from overlore.ws import handle_client_connection

SUBSCRIPTIONS_WITH_CALLBACKS: list[tuple[Subscriptions, OnEventCallbackType]] = [
    (Subscriptions.COMBAT_OUTCOME, process_received_event),
    (Subscriptions.ORDER_ACCEPTED, process_received_event),
    (Subscriptions.NPC_SPAWNED, delete_npc_from_db),
]

logger = logging.getLogger("overlore")


async def use_prompt_loop(config: BootConfig) -> None:
    mock_response = json.dumps(MOCK_KATANA_RESPONSE)
    with responses.RequestsMock() as rsps:
        rsps.add(rsps.POST, config.env["KATANA_URL"], body=mock_response, status=200)
        rsps.add_passthru(GUARD_RAILS_HUB_URL)
        while True:
            txt = input("hit enter to generate townhall with realm_id 73 or enter realm_id\n")
            realm_id = 73 if len(txt) == 0 else int(txt)
            msg = f'{{"realm_id": {realm_id}, "order_id": 1, "npcs" : {json.dumps(MOCK_VILLAGERS)}}}'
            res = cast(WsTownhallResponse, handle_townhall_request(json.loads(msg), config=config))
            logger.debug(f"______GPT answer______\n{res['dialogue']}\n________________________\n\n\n\n\n\n\n\n")


async def cancel_all_tasks() -> None:
    subscriptions_names = [sub.name for (sub, _) in SUBSCRIPTIONS_WITH_CALLBACKS]
    tasks = [task for task in asyncio.all_tasks() if task.get_name() in subscriptions_names]
    for task in tasks:
        logger.info(f"Cancelling task: {task.get_name()}")
        task.cancel()


def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
    logger.info("Shutting down Overlore ...")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    asyncio.run_coroutine_threadsafe(cancel_all_tasks(), loop=asyncio.get_running_loop())


def setup() -> BootConfig:
    config = BootConfig()

    signal.signal(signal.SIGINT, handle_sigint)

    if config.mock is True:
        EventsDatabase.instance().init(":memory:")
        TownhallDatabase.instance().init(":memory:")
        NpcDatabase.instance().init(":memory:")
    else:
        EventsDatabase.instance().init()
        TownhallDatabase.instance().init()
        NpcDatabase.instance().init()

    os.environ["GUARDRAILS_PROCESS_COUNT"] = "30"

    return config


async def launch_services(config: BootConfig) -> None:
    handle_client_connection_bound_handler = functools.partial(handle_client_connection, config=config)

    overlore_server = await serve(
        handle_client_connection_bound_handler, config.env["HOST_ADDRESS"], int(config.env["HOST_PORT"])
    )

    logger.info(
        f"great job, starting this service on port {config.env['HOST_PORT']}. everything is perfect from now on."
    )

    try:
        await use_torii_subscription(config.env["TORII_WS"], SUBSCRIPTIONS_WITH_CALLBACKS)
    except ConnectionClosedError:
        logger.warning("Connection close on Torii, need to reconnect here")
    finally:
        overlore_server.close()
        await overlore_server.wait_closed()


async def start() -> None:
    config = setup()

    if config.prompt:
        global SUBSCRIPTIONS_WITH_CALLBACKS
        SUBSCRIPTIONS_WITH_CALLBACKS = [(Subscriptions.NONE, use_prompt_loop)]  # type: ignore[list-item]
        task = asyncio.create_task(use_prompt_loop(config=config))
        await asyncio.wait_for(task, None)
        return

    # Sync events database on boot
    await torii_boot_sync(torii_service_endpoint=config.env["TORII_GRAPHQL"])

    if config.mock is True:
        await with_mock_responses(launch_services, config, config)
    else:
        await launch_services(config=config)


# hardcode for now, when more mature we need some plumbing to read this off a config
def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
