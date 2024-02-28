import json
import logging
from typing import Any, cast

import requests

from overlore.types import MsgType, WsData

logger = logging.getLogger("overlore")


def get_ws_msg_type(message: WsData) -> MsgType:
    return cast(MsgType, message.get("type"))


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


async def get_katana_timestamp(katana_url: str) -> Any:
    data = {"jsonrpc": "2.0", "method": "starknet_getBlockWithTxs", "params": {"block_id": "latest"}, "id": 1}
    ret = await query_katana_node(katana_url, data)
    return ret.get("result").get("timestamp")


async def query_katana_node(katana_url: str, data: dict[str, Any]) -> Any:
    # Define the URL and the header
    headers = {"Content-Type": "application/json"}

    # Make the POST request
    response = requests.post(katana_url, headers=headers, data=json.dumps(data), timeout=1000)
    # throws
    json_response = str_to_json(response.text)
    return json_response
