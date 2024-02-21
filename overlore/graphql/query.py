import logging
from typing import Any

import requests

logger = logging.getLogger("overlore")


def run_torii_query(torii_endpoint: str, query: str) -> Any:
    data = None
    try:
        response = requests.post(torii_endpoint, json={"query": query}, timeout=5)
        json_response = response.json()
        data = json_response["data"]
    except KeyError as e:
        logger.error("KeyError accessing %s in JSON response: %s", e, json_response)
    if data is None:
        raise RuntimeError(f"Failed to run query {json_response['errors']}")
    return data
