import asyncio
import threading

from aiohttp import web
from aiohttp_cors import ResourceOptions
from aiohttp_cors import setup as cors_setup
from jsonrpcserver import async_dispatch

from overlore.config import BootConfig


async def handle(request):
    return web.Response(text=await async_dispatch(await request.text()), content_type="application/json")


def create_aiohttp_server():
    app = web.Application()

    routes = [web.post("/", handle)]
    app.router.add_routes(routes)
    cors = cors_setup(
        app,
        defaults={
            "*": ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )

    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    return runner


def launch_json_rpc_server_loop(runner, config: BootConfig):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, config.env["HOST_ADDRESS"], config.env["HOST_PORT"])
    loop.run_until_complete(site.start())
    loop.run_forever()


def launch_json_rpc_server(config: BootConfig):
    json_rpc_thread = threading.Thread(
        target=launch_json_rpc_server_loop,
        args=(
            create_aiohttp_server(),
            config,
        ),
    )
    json_rpc_thread.daemon = True

    json_rpc_thread.start()
