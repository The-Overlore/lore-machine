import json


def msg_to_json(message: str):
    try:
        return json.loads(message)
    except Exception as error:
        print(f"invalid message received by ws: {error}")
        return {}
