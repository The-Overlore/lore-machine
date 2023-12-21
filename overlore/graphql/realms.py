from typing import List, TypedDict

import requests


class RealmData(TypedDict):
    realm_id: str
    entity_id: str


all_realms_query = """
    query AllRealmsForYourMomma {{
        realmModels {{
          edges {{
            node {{
              realm_id
              entity_id
           }}
         }}
       }}
     }}
"""

# Main Synchronization Function
def fetch_realms(graphql_endpoint: str) -> List[RealmData]:
    response = requests.post(graphql_endpoint, json={"query": all_realms_query}, timeout=5)
    data = response.json()
    if "data" in data and "realmModels" in data["data"]:
        edges = data["data"]["realmModels"]["edges"]
        return [node["node"] for node in edges]
    else:
        return []
