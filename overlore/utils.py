import argparse
import json
from argparse import Namespace
from typing import Any


def str_to_json(message: str) -> Any:
    try:
        return json.loads(message)
    except Exception as error:
        print(f"invalid string: {error}")
        return {}


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


def get_enum_name_by_value(enum: Any, val: Any) -> Any:
    for enum_entry in enum:
        if enum_entry.value == val:
            return enum_entry.name
    return None  # Return None or raise an error if the value is not found
