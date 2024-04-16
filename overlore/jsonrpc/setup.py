import asyncio
import threading

from aiohttp import web
from aiohttp_cors import ResourceOptions
from aiohttp_cors import setup as cors_setup
from jsonrpcserver import async_dispatch

from overlore.config import BootConfig
from overlore.jsonrpc.types import JsonRpcMethod
from overlore.jsonrpc.utils import snake_to_camel

methods_key: web.AppKey = web.AppKey(name="methods", t=JsonRpcMethod)


async def handle_http_request(request: web.Request) -> web.Response:
    methods = request.app[methods_key]

    dispatch_methods = {f"{snake_to_camel(method['method'].__name__)}": method["method"] for method in methods}

    request_as_json = await request.json()

    method_called = next(
        filter(lambda method: snake_to_camel(method["method"].__name__) == request_as_json["method"], methods), None
    )

    if method_called is None:
        return web.Response(status=404)

    return web.Response(
        text=await async_dispatch(
            await request.text(),
            methods=dispatch_methods,
            context=method_called["context"],
        ),
        content_type="application/json",
    )


def launch_json_rpc_server(methods: list[JsonRpcMethod], config: BootConfig) -> None:
    json_rpc_thread = threading.Thread(
        target=launch_json_rpc_server_loop,
        args=(
            create_aiohttp_server(methods=methods),
            config,
        ),
    )
    json_rpc_thread.daemon = True

    json_rpc_thread.start()


def launch_json_rpc_server_loop(runner: web.AppRunner, config: BootConfig) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, config.env["HOST_ADDRESS"], int(config.env["HOST_PORT"]))
    loop.run_until_complete(site.start())
    loop.run_forever()


def create_aiohttp_server(methods: list[JsonRpcMethod]) -> web.AppRunner:
    app = web.Application()

    app[methods_key] = methods

    routes = [web.post("/", handle_http_request)]
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
