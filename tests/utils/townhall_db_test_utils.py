from overlore.sqlite.townhall_db import TownhallDatabase

given_townhall_values = [
    {"rowid": i, "discussion": f"Discussion {i}", "input": f"Input {i}", "realm_id": i * 100, "ts": i * 1000}
    for i in range(1, 4)
]

given_townhall_values_for_single_realm = [
    {"discussion": f"Discussion {i}", "input": f"Input {i}", "ts": i * 1000} for i in range(1, 4)
]

given_plots = [{"rowid": i, "realm_id": i, "plot": f"plot {i}"} for i in range(1, 4)]

given_update_plots = [{"rowid": i, "realm_id": i, "new_plot": f"new plot {i}"} for i in range(1, 4)]

given_thoughts = [
    {"rowid": i, "npc_entity_id": i * 100, "thought": f"Thought {i}", "poignancy": i, "ts": i, "embedding": [0.1]}
    for i in range(1, 4)
]

daily_town_hall_tracker_data = [
    {
        "row_id": i,
        "realm_id": i * 10,
        "event_row_id": i * 5,
    }
    for i in range(1, 4)
]


def generate_townhalls_for_realmid(db, realm_id, townhalls):
    for item in townhalls:
        db.insert_townhall_discussion(realm_id, item["discussion"], item["input"], item["ts"])


def format_townhalls(townhalls) -> list:
    res = []
    for item in townhalls:
        res.insert(0, (item["discussion"], item["input"]))
    return res


def prepare_daily_town_hall_tracker_data(db):
    for item in daily_town_hall_tracker_data:
        db.insert_or_update_daily_townhall_tracker(item["realm_id"], item["event_row_id"])


class ThoughtsDatabaseFiller:
    def __init__(self, database: TownhallDatabase):
        self.database = database

    def populate_with_time_increase(self, num: int) -> int:
        last_inserted_id = 0
        embedded_vector = [1.0] * 1536
        for i in range(1, num + 1):
            last_inserted_id = self.database.insert_npc_thought(
                npc_entity_id=1, thought=f"{i}", poignancy=1, katana_ts=i, thought_embedding=embedded_vector
            )

        return last_inserted_id

    def populate_with_cosine_increase(self, num: int) -> int:
        last_inserted_id = 0

        for i in range(1, num + 1):
            embedded_vector = [float(i)] + ([float(100)] * 1535)
            last_inserted_id = self.database.insert_npc_thought(
                npc_entity_id=1, thought=f"{i}", poignancy=1, katana_ts=1, thought_embedding=embedded_vector
            )
        return last_inserted_id

    def populate_with_poignancy_increase(self, num: int) -> int:
        last_inserted_id = 0
        embedded_vector = [1.0] * 1536

        for i in range(1, num + 1):
            last_inserted_id = self.database.insert_npc_thought(
                npc_entity_id=1, thought=f"{i}", poignancy=i, katana_ts=1, thought_embedding=embedded_vector
            )
        return last_inserted_id
