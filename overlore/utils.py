import json
import logging
from typing import Any, List

import requests

# probably can be brought to its own directory
from starknet_py.hash.utils import verify_message_signature

logger = logging.getLogger("overlore")


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


def calculate_message_hash(payload: str) -> Any:
    # TODO
    return "Ligma"


def is_valid_message(payload: str, signature: List[int], public_key: int) -> bool:
    """
    Validates the message by verifying its signature against the payload and the provided public key.

    Args:
        payload (str): The message payload.
        signature (List[int]): The message signature as a list of integers.
        public_key (int): The public key provided by the sender.

    Returns:
        bool: True if the message is valid, False otherwise.
    """
    # Convert the payload into a hash suitable for StarkNet
    # TODO
    msg_hash = calculate_message_hash(payload)  #

    # Verify the message signature using StarkNet's verification function
    return verify_message_signature(msg_hash, signature, public_key)
