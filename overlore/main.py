import asyncio
import logging
import signal
import time
from types import FrameType

from overlore.config import BootConfig
from overlore.jsonrpc.constants import setup_json_rpc_methods
from overlore.jsonrpc.setup import launch_json_rpc_server
from overlore.mocks import setup_mock_json_rpc_methods
from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.events_db import EventsDatabase
from overlore.sqlite.npc_db import NpcDatabase
from overlore.torii.client import ToriiClient
from overlore.torii.subscriptions import TORII_SUBSCRIPTIONS, use_torii_subscription

logger = logging.getLogger("overlore")


async def cancel_all_tasks() -> None:
    subscriptions_names = [sub.name for (sub, _) in TORII_SUBSCRIPTIONS]
    tasks = [task for task in asyncio.all_tasks() if task.get_name() in subscriptions_names]
    for task in tasks:
        logger.info(f"Cancelling task: {task.get_name()}")
        task.cancel()


def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
    logger.info("Shutting down Overlore ...")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    asyncio.run_coroutine_threadsafe(cancel_all_tasks(), loop=asyncio.get_running_loop())
    exit(0)


def setup() -> BootConfig:
    signal.signal(signal.SIGINT, handle_sigint)

    config = BootConfig()

    if config.mock:
        EventsDatabase.instance().init(":memory:")
        DiscussionDatabase.instance().init(":memory:")
        NpcDatabase.instance().init(":memory:")
    else:
        EventsDatabase.instance().init()
        DiscussionDatabase.instance().init()
        NpcDatabase.instance().init()

    return config


async def launch_services(config: BootConfig) -> None:
    json_rpc_methods = setup_mock_json_rpc_methods() if config.mock else setup_json_rpc_methods(config=config)
    launch_json_rpc_server(methods=json_rpc_methods, config=config)

    logger.info(f"Starting JSON-RPC server on {config.env['HOST_ADDRESS']}:{config.env['HOST_PORT']}")

    if config.mock is False:
        await use_torii_subscription(config=config, callback_and_subs=TORII_SUBSCRIPTIONS)
    else:
        while True:
            time.sleep(2)


async def sync_services(config: BootConfig) -> None:
    torii_client = ToriiClient(url=config.env["TORII_GRAPHQL"])
    await torii_client.boot_sync()


async def start() -> None:
    config = setup()

    if config.mock is False:
        await sync_services(config=config)

    await launch_services(config=config)


def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
