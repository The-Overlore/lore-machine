from typing import List, TypedDict

import requests

from overlore.graphql.constants import Queries


class RealmData(TypedDict):
    realm_id: str
    entity_id: str


# Main Synchronization Function
def fetch_realms(graphql_endpoint: str) -> List[RealmData]:
    response = requests.post(graphql_endpoint, json={"query": Queries.ALL_REALMS.value}, timeout=5)
    data = response.json()
    if "data" in data and "realmModels" in data["data"]:
        edges = data["data"]["realmModels"]["edges"]
        return [node["node"] for node in edges]
    else:
        return []
