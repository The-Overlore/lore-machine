import asyncio
import json
import logging
import os
import signal
from types import FrameType

import responses
from jsonrpcserver import Success

from overlore.config import BootConfig, global_config
from overlore.graphql.client import ToriiClient
from overlore.graphql.subscriptions import (
    OnEventCallbackType,
    Subscriptions,
    process_received_event,
    process_received_spawn_npc_event,
    use_torii_subscription,
)
from overlore.jsonrpc.methods.generate_town_hall.generate_town_hall import generate_town_hall
from overlore.jsonrpc.setup import launch_json_rpc_server
from overlore.llm.constants import GUARD_RAILS_HUB_URL
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.sqlite.townhall_db import TownhallDatabase
from overlore.townhall.mocks import MOCK_KATANA_RESPONSE, MOCK_VILLAGERS, with_mock_responses

SUBSCRIPTIONS_WITH_CALLBACKS: list[tuple[Subscriptions, OnEventCallbackType]] = [
    (Subscriptions.COMBAT_OUTCOME, process_received_event),
    (Subscriptions.ORDER_ACCEPTED, process_received_event),
    (Subscriptions.NPC_SPAWNED, process_received_spawn_npc_event),
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
            res: Success = generate_town_hall(json.loads(msg), config=config)
            logger.debug(res)


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


def setup(config: BootConfig):
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
    launch_json_rpc_server(config=config)

    logger.info(f"Starting JSON-RPC server on {config.env['HOST_ADDRESS']}:{config.env['HOST_PORT']}")

    await use_torii_subscription(
        torii_service_endpoint=config.env["TORII_WS"], callback_and_subs=SUBSCRIPTIONS_WITH_CALLBACKS
    )


async def start(config: BootConfig) -> None:
    setup(config=config)

    if config.prompt:
        global SUBSCRIPTIONS_WITH_CALLBACKS
        SUBSCRIPTIONS_WITH_CALLBACKS = [(Subscriptions.NONE, use_prompt_loop)]  # type: ignore[list-item]
        task = asyncio.create_task(use_prompt_loop(config=config))
        await asyncio.wait_for(task, None)
        return

    torii_client = ToriiClient(torii_url=config.env["TORII_GRAPHQL"], events_db=EventsDatabase.instance())
    await torii_client.boot_sync()

    if config.mock is True:
        await with_mock_responses(launch_services, config, config)
    else:
        await launch_services(config=config)


def main() -> None:
    asyncio.run(start(config=global_config))


if __name__ == "__main__":
    main()
