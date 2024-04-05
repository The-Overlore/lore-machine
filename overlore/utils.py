import logging
from typing import Any, Sequence, cast

from starknet_py.cairo.felt import encode_shortstring
from starknet_py.hash.utils import ECSignature, message_signature
from starknet_py.hash.utils import compute_hash_on_elements as pedersen

from overlore.eternum.constants import ResourceNamesById
from overlore.types import Characteristics

logger = logging.getLogger("overlore")

U2_MASK: int = 0x3
U8_MASK: int = 0xFF


def get_ressource_name_by_id(resource_id: Any) -> str:
    if resource_id in ResourceNamesById:
        return ResourceNamesById[resource_id]
    else:
        raise RuntimeError(f"No resource found for ID {resource_id}")


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
