import json
import logging
from typing import Any, Sequence, cast

import aiohttp
from starknet_py.cairo.felt import encode_shortstring
from starknet_py.hash.utils import ECSignature, message_signature
from starknet_py.hash.utils import compute_hash_on_elements as pedersen

from overlore.types import Characteristics

logger = logging.getLogger("overlore")

U2_MASK: int = 0x3
U8_MASK: int = 0xFF


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


async def get_katana_timestamp(katana_url: str) -> int:
    data = {"jsonrpc": "2.0", "method": "starknet_getBlockWithTxs", "params": {"block_id": "latest"}, "id": 1}
    ret = await query_katana_node(katana_url, data)
    return cast(int, ret.get("result").get("timestamp"))


async def query_katana_node(katana_url: str, data: dict[str, Any]) -> Any:
    # Define the URL and the header
    headers = {"Content-Type": "application/json"}

    # Make the POST request
    async with aiohttp.ClientSession() as session:
        async with session.post(url=katana_url, headers=headers, data=json.dumps(data), timeout=1000) as response:
            response = await response.json()
    return response


def sign_parameters(msg: Sequence, priv_key: str) -> ECSignature:
    msg_felt = [encode_shortstring(elem) if isinstance(elem, str) else elem for elem in msg]
    msg_hash = pedersen(msg_felt)
    return message_signature(msg_hash, int(priv_key, base=16))


def unpack_characteristics(characteristics: int) -> Characteristics:
    age: int = characteristics & U8_MASK
    characteristics >>= 8
    role: int = characteristics & U8_MASK
    characteristics >>= 8
    sex: int = characteristics & U2_MASK

    return cast(
        Characteristics,
        {
            "age": age,
            "role": role,
            "sex": sex,
        },
    )
