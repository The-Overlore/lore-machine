import json
import logging
from typing import Any, Sequence, cast

import requests
from starknet_py.cairo.felt import encode_shortstring
from starknet_py.hash.utils import ECSignature, message_signature
from starknet_py.hash.utils import compute_hash_on_elements as pedersen

from overlore.types import MsgType, WsIncomingMsg

logger = logging.getLogger("overlore")


def get_ws_msg_type(message: WsIncomingMsg) -> MsgType:
    return cast(MsgType, message["msg_type"])


def str_to_json(message: str) -> Any:
    try:
        return json.loads(message)
    except Exception as error:
        logger.exception(f"invalid string: {error}")
        raise


def open_json_file(path: str) -> Any:
    # Read the JSON data from the file
    with open(path) as file:
        file_contents = json.load(file)
        return file_contents


def get_enum_name_by_value(enum: Any, val: Any) -> str:
    for enum_entry in enum:
        if enum_entry.value == val:
            return str(enum_entry.name)
    raise RuntimeError(f"No value for val {val} in enum")


async def get_contract_nonce(katana_url: str, contract_address: str) -> int:
    data = {
        "jsonrpc": "2.0",
        "method": "starknet_getNonce",
        "params": {"block_id": "latest", "contract_address": contract_address},
        "id": 1,
    }
    ret = await query_katana_node(katana_url, data)
    return cast(int, ret.get("result"))


async def get_katana_timestamp(katana_url: str) -> int:
    data = {"jsonrpc": "2.0", "method": "starknet_getBlockWithTxs", "params": {"block_id": "latest"}, "id": 1}
    ret = await query_katana_node(katana_url, data)
    return cast(int, ret.get("result").get("timestamp"))


async def query_katana_node(katana_url: str, data: dict[str, Any]) -> Any:
    # Define the URL and the header
    headers = {"Content-Type": "application/json"}

    # Make the POST request
    response = requests.post(katana_url, headers=headers, data=json.dumps(data), timeout=1000)
    # throws
    json_response = str_to_json(response.text)
    return json_response


def sign_parameters(msg: Sequence, priv_key: str) -> ECSignature:
    msg_felt = [encode_shortstring(elem) if type(elem) == str else elem for elem in msg]
    msg_hash = pedersen(msg_felt)

    return message_signature(msg_hash, int(priv_key, base=16))
