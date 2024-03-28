from overlore.utils import query_katana_node


async def get_contract_nonce(katana_url: str, contract_address: str) -> int:
    data = {
        "jsonrpc": "2.0",
        "method": "starknet_getNonce",
        "params": {"block_id": "latest", "contract_address": contract_address},
        "id": 1,
    }
    ret = await query_katana_node(katana_url, data)
    return int(ret.get("result"), base=16)
