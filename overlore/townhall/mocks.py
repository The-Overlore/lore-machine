import json
import os


def load_mock_villagers():
    # Get the current file's directory
    current_dir = os.path.dirname(__file__)

    # Build the path to the events.json file
    villagers_path = os.path.join(current_dir, "../../data/villagers.json")

    # Read the JSON data from the file
    with open(villagers_path) as file:
        villagers = json.load(file)

    return villagers


def load_mock_events():
    # Get the current file's directory
    current_dir = os.path.dirname(__file__)

    # Build the path to the events.json file
    events_path = os.path.join(current_dir, "../../data/events.json")

    # Read the JSON data from the file
    with open(events_path) as file:
        events = json.load(file)

    # Use a list comprehension to extract eventEmitted details
    processed_events = [
        [event.get("data", {}).get("eventEmitted", {}) for event in event_group] for event_group in events
    ]

    return processed_events


def fetch_villagers():
    return load_mock_villagers()


# as in FAKE
def fetch_users(index: int):
    # Mock user data
    users = ["User1", "User2", "User3"]
    return users[index]


# as in FAKE news
def fetch_events(index: int):
    # Mock event data
    return load_mock_events()[index]
