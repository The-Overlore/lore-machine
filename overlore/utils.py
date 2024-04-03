import json
import logging
from typing import Any, Sequence, cast

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
