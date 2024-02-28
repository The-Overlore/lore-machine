import asyncio
import functools
import json
import logging
import signal
from types import FrameType
from typing import cast

import responses
from websockets import WebSocketServerProtocol, serve
from websockets.exceptions import ConnectionClosedError

from overlore.config import BootConfig
from overlore.graphql.boot_sync import torii_boot_sync
from overlore.graphql.constants import Subscriptions
from overlore.graphql.subscriptions import (
    assign_name_character_trait_to_npc,
    process_received_event,
    torii_subscription_connection,
)
from overlore.llm.open_ai import OpenAIHandler
from overlore.npcs.spawn import spawn_npc
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.vector_db import VectorDatabase
from overlore.townhall.logic import handle_townhall_request
from overlore.townhall.mocks import MOCK_KATANA_RESPONSE, MOCK_VILLAGERS
from overlore.types import MsgType
from overlore.utils import get_ws_msg_type, str_to_json

logger = logging.getLogger("overlore")

EVENT_SUBS_AND_CALLBACKS = [
    (Subscriptions.COMBAT_OUTCOME, process_received_event),
    (Subscriptions.ORDER_ACCEPTED, process_received_event),
    (Subscriptions.NPC_SPAWNED, assign_name_character_trait_to_npc),
]


async def prompt_loop(config: BootConfig) -> None:
    test_url = config.env["KATANA_URL"]
    mock_response = json.dumps(MOCK_KATANA_RESPONSE)
    with responses.RequestsMock() as rsps:
        rsps.add(rsps.POST, test_url, body=mock_response, status=200)
        while True:
            txt = input("hit enter to generate townhall with realm_id 73 or enter realm_id\n")
            realm_id = 73 if len(txt) == 0 else int(txt)
            msg = f'{{"realm_id": {realm_id}, "orderId": 1, "npcs" : {json.dumps(MOCK_VILLAGERS)}}}'
            (rowid, townhall, systemPrompt, userPrompt) = await handle_townhall_request(json.loads(msg), config=config)
            logger.debug(f"______System prompt______\n{systemPrompt}\n________________________")
            logger.debug(f"______User prompt______\n{userPrompt}\n________________________")
            logger.debug(f"______GPT answer______\n{townhall}\n________________________\n\n\n\n\n\n\n\n")


async def cancel_all_tasks() -> None:
    subscriptions_names = [sub.name for (sub, _) in EVENT_SUBS_AND_CALLBACKS]
    tasks = [task for task in asyncio.all_tasks() if task.get_name() in subscriptions_names]
    for task in tasks:
        logger.info(f"Cancelling task: {task.get_name()}")
        task.cancel()


def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
    logger.info("Shutting down Overlore ...")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    asyncio.run_coroutine_threadsafe(cancel_all_tasks(), loop=asyncio.get_running_loop())


async def service(websocket: WebSocketServerProtocol, config: BootConfig) -> None:
    async for message in websocket:
        response: dict[str, int | str] = {}
        if message is None:
            continue
        logger.debug("generating townhall")
        try:
            data = str_to_json(cast(str, message))
        except Exception as error:
            await websocket.send(json.dumps(response))
            response = {"type": MsgType.ERROR.value, "reason": f"Failure to generate a dialog: {error}"}
        ws_msg_type = get_ws_msg_type(data)
        if ws_msg_type == MsgType.TOWNHALL.value:
            (rowid, response, _, _) = await handle_townhall_request(data, config)
            response = {"type": MsgType.TOWNHALL.value, "id": rowid, "townhall": response}
        elif ws_msg_type == MsgType.SPAWN_NPC.value:
            npc_profile = await spawn_npc(data)
            response = {"type": MsgType.SPAWN_NPC.value, "npc": npc_profile}
            logger.debug(response)
        await websocket.send(json.dumps(response))


def setup() -> BootConfig:
    config = BootConfig()

    signal.signal(signal.SIGINT, handle_sigint)

    EventsDatabase.instance().init()
    VectorDatabase.instance().init()

    OpenAIHandler.instance().init(config.env["OPENAI_API_KEY"])
    return config


async def launch_services(config: BootConfig) -> None:
    service_bound_handler = functools.partial(service, config=config)

    overlore_server = await serve(service_bound_handler, config.env["HOST_ADDRESS"], int(config.env["HOST_PORT"]))

    logger.info(
        f"great job, starting this service on port {config.env['HOST_PORT']}. everything is perfect from now on."
    )

    try:
        await torii_subscription_connection(config.env["TORII_WS"], EVENT_SUBS_AND_CALLBACKS)
    except ConnectionClosedError:
        logger.warning("Connection close on Torii, need to reconnect here")
    finally:
        overlore_server.close()
        await overlore_server.wait_closed()


async def start() -> None:
    config = setup()

    if config.prompt:
        await prompt_loop(config)

    # Sync events database on boot
    await torii_boot_sync(config.env["TORII_GRAPHQL"])

    await launch_services(config)


# hardcode for now, when more mature we need some plumbing to read this off a config
def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
