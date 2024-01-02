from tinydb import TinyDB

from overlore.graphql.constants import EventType


class DatabaseHandler:
    path: str
    db: TinyDB = None
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            print("Creating db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self, openai_api_key, openai_embeddings_api_key):
        raise RuntimeError("Call instance() instead")

    def init(self, path: str = "./events_db.json"):
        self.db = TinyDB(path)
        return self

    def get_by_id(self, doc_id: int):
        return self.db.get(doc_id=doc_id)

    def __add(self, obj):
        return self.db.insert(obj)

    def __get_event_type(self, obj):
        return obj.get("eventEmitted").get("keys")[0]

    def __parse_resources(self, data: []):
        resource_len = int(data[0], base=16)
        end_idx_resources = resource_len * 2
        resources = [
            {"type": int(data[i], base=16), "amount": int(int(data[i + 1], base=16) / 1000)}
            for i in range(1, end_idx_resources, 2)
        ]
        return (data[end_idx_resources + 1 :], resources)

    def __parse_attacking_entity_ids(self, data):
        length = int(data[0], base=16)
        attacking_entity_ids = [int(data[i], base=16) for i in range(1, length)]
        return (data[1 + length :], attacking_entity_ids)

    def __parse_combat_outcome_event(self, event):
        keys = event.get("eventEmitted").get("keys")
        data = event.get("eventEmitted").get("data")

        attacker_realm_id = int(keys[1], base=16)
        target_realm_entity_id = int(keys[2], base=16)

        (data, attacking_entity_ids) = self.__parse_attacking_entity_ids(data)
        (data, stolen_resources) = self.__parse_resources(data)

        winner = int(data[0], base=16)
        damage = int(data[1], base=16)
        ts = int(data[2], base=16)

        parsed_event = {
            "attacker_realm_id": attacker_realm_id,
            "target_realm_entity_id": target_realm_entity_id,
            "attacking_entity_ids": attacking_entity_ids,
            "stolen_resources": stolen_resources,
            "winner": winner,
            "damage": damage,
            "ts": ts,
        }
        return parsed_event

    def __parse_trade_event(self, event):
        keys = event.get("eventEmitted").get("keys")
        data = event.get("eventEmitted").get("data")

        trade_id = int(keys[1], base=16)
        maker_id = int(data[0], base=16)
        taker_id = int(data[1], base=16)

        data = data[2:]

        (data, resources_maker) = self.__parse_resources(data)
        (data, resources_taker) = self.__parse_resources(data)
        ts = int(data[0], base=16)

        parsed_event = {
            "trade_id": trade_id,
            "maker_id": maker_id,
            "taker_id": taker_id,
            "resources_maker": resources_maker,
            "resources_taker": resources_taker,
            "ts": ts,
        }
        return parsed_event

    def process_event(self, event):
        if self.__get_event_type(event) == EventType.COMBAT_OUTCOME.value:
            parsed_event = self.__parse_combat_outcome_event(event)
        else:
            parsed_event = self.__parse_trade_event(event)
        return self.__add(parsed_event)
