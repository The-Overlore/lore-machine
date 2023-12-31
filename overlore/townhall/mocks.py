from typing import Any

from overlore.utils import open_json_file


async def load_mock_gpt_response(mock_index: int) -> str:
    gpt_response_file = open_json_file("./data/mock_gpt_response.json")
    try:
        return str(gpt_response_file[mock_index].get("message"))
    except Exception as error:
        print(error)
        return ""


def load_mock_villagers() -> Any:
    return open_json_file("./data/villagers.json")


def load_mock_events() -> Any:
    events = open_json_file("./data/events.json")
    # Use a list comprehension to extract eventEmitted details
    processed_events = [
        [event.get("data", {}).get("eventEmitted", {}) for event in event_group] for event_group in events
    ]

    return processed_events


def fetch_villagers() -> Any:
    return load_mock_villagers()


# as in FAKE
def fetch_users(index: int) -> Any:
    # Mock user data
    users = ["User1", "User2", "User3"]
    return users[index]


# as in FAKE news
def fetch_events(index: int) -> Any:
    # Mock event data
    return load_mock_events()[index]
