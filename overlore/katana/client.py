import json
from typing import Any, cast

import aiohttp

from overlore.errors import ErrorCodes


class KatanaClient:
    def __init__(self, url: str):
        self.url = url

    async def get_contract_nonce(self, contract_address: str) -> int:
        params = {"block_id": "latest", "contract_address": contract_address}
        ret = await self._query_katana_node(method="starknet_getNonce", params=params)
        return int(ret.get("result"), base=16)

    async def get_katana_ts(self) -> int:
        params = {"block_id": "latest"}

        ret = await self._query_katana_node(method="starknet_getBlockWithTxs", params=params)
        return cast(int, ret.get("result").get("timestamp"))

    async def _query_katana_node(self, method: str, params: dict[str, Any]) -> Any:
        try:
            headers = {"Content-Type": "application/json"}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=self.url,
                    headers=headers,
                    data=json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "method": method,
                            "params": params,
                            "id": 1,
                        }
                    ),
                    timeout=1000,
                ) as response:
                    response = await response.json()
        except aiohttp.ClientConnectorError as err:
            raise RuntimeError(ErrorCodes.KATANA_UNAVAILABLE) from err
        return response
