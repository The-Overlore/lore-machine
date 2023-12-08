import json
import os


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
        event.get("data", {}).get("eventEmitted", {}) for event_group in events for event in event_group
    ]

    return processed_events


# as in FAKE
def fetch_users():
    # Mock user data
    users = ["User1", "User2", "User3"]
    return users


# as in FAKE news
def fetch_events():
    # Mock event data
    return load_mock_events()
