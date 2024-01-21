import argparse
import json
from argparse import Namespace
from typing import Any

import requests


def str_to_json(message: str) -> Any:
    try:
        return json.loads(message)
    except Exception as error:
        print(f"invalid string: {error}")
        raise


def open_json_file(path: str) -> Any:
    # Read the JSON data from the file
    with open(path) as file:
        file_contents = json.load(file)
        return file_contents


def parse_cli_args() -> Namespace:
    parser = argparse.ArgumentParser(description="The weaving loomer of all possible actual experiential occasions.")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data for GPT response instead of querying the API. (saves API calls)",
    )
    parser.add_argument("-a", "--address", help="Host address for connection", type=str, default="localhost")
    return parser.parse_args()


def get_enum_name_by_value(enum: Any, val: Any) -> str:
    for enum_entry in enum:
        if enum_entry.value == val:
            return str(enum_entry.name)
    raise RuntimeError(f"No value for val {val} in enum")


async def get_katana_timestamp() -> Any:
    data = {"jsonrpc": "2.0", "method": "starknet_getBlockWithTxs", "params": {"block_id": "latest"}, "id": 1}
    ret = await query_katana_node(data)
    return ret.get("result").get("timestamp")


async def query_katana_node(data: dict[str, Any]) -> Any:
    # Define the URL and the header
    url = "http://localhost:5050"
    headers = {"Content-Type": "application/json"}

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=1000)
    # throws
    json_response = str_to_json(response.text)
    return json_response
