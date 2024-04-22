import asyncio
import json
import random
from typing import Any, cast

import aiohttp

from overlore.constants import MAX_AGE, MIN_AGE, ROLES, SEX


class MockRandGenerator:
    def __init__(self, seed):
        self.rand = random.Random(seed)

    def generate_age(self) -> int:
        return self.rand.randint(MIN_AGE, MAX_AGE)

    def generate_sex(self) -> int:
        return self.rand.randint(0, len(SEX) - 1)

    def generate_role(self) -> int:
        return self.rand.randint(0, len(ROLES) - 1)


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
