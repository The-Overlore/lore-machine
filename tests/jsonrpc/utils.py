import asyncio
import json
from typing import Any, cast

import aiohttp


def run_async_function(async_function: Any, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    _ = loop.run_until_complete(async_function(*args, **kwargs))
    loop.close()


async def call_json_rpc_server(url: str, method: str, params: Any, storing_object: list[Any] | None = None):
    headers = {"Content-Type": "application/json"}
    data_string = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": method,
            "params": [params],
            "id": 1,
        }
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=url,
                headers=headers,
                data=data_string,
                timeout=1000,
            ) as response:
                json_response = cast(dict[str, Any], await response.json())
        if storing_object is not None:
            storing_object.append(json_response)
        else:
            return json_response
    except Exception as a:
        raise RuntimeError(a) from a
