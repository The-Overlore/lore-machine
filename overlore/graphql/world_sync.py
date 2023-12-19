import os

import requests
from dotenv import load_dotenv

load_dotenv()

# GraphQL Client Initialization
TORII_ENDPOINT = os.environ.get("TORII_ENDPOINT")

# Constants from
# https://github.com/edisontim/eternum-tedison/blob/client-with-contracts/client/src/hooks/graphql/useGraphQLQueries.tsx#L102
OFFSET = 100
COMPONENT_INTERVAL = 37

# Helper Functions
def build_query(component_names, cursor):
    models_query_builder = ""
    for component_name in component_names:
        # Add details as per your schema
        models_query_builder += f"... on {component_name} {{ __typename ... }}"

    return f"""
        query SyncWorld {{
            entities: entities(keys:["%"] {f'after: "{cursor}"' if cursor else ""} first: {OFFSET}) {{
                total_count
                edges {{
                    cursor
                    node {{
                        keys
                        id
                        models {{
                            {models_query_builder}
                        }}
                    }}
                }}
            }}
        }}"""


# Main Synchronization Function
async def sync_world():
    progress = 0

    component_names = ["Component1", "Component2"]  # need to reflect on world component names
    cursor = None

    try:
        while True:
            query = build_query(component_names, cursor)
            response = requests.post(TORII_ENDPOINT, json={"query": query}, timeout=5)
            data = response.json()

            entities = data["data"]["entities"]
            total_count = entities["total_count"]
            edges = entities["edges"]

            # Process your data here...

            if len(edges) < OFFSET:
                break
            else:
                cursor = edges[-1]["cursor"]

            # Update progress
            progress = min(progress + OFFSET, total_count)
            print(f"Progress: {progress / total_count * 100}%")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        pass
