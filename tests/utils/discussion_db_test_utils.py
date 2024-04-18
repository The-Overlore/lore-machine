from overlore.sqlite.discussion_db import DiscussionDatabase

given_discussion_values_for_single_realm = [
    {"discussion": f"Discussion {i}", "input": f"Input {i}", "input_score": i, "ts": i * 1000} for i in range(1, 4)
]

given_plots = [{"rowid": i, "realm_id": i, "plot": f"plot {i}"} for i in range(1, 4)]

given_update_plots = [{"rowid": i, "realm_id": i, "new_plot": f"new plot {i}"} for i in range(1, 4)]

given_thoughts = [
    {"rowid": i, "npc_entity_id": i * 100, "thought": f"Thought {i}", "poignancy": i, "ts": i, "embedding": [0.1]}
    for i in range(1, 4)
]

daily_discussion_tracker_data = [
    {
        "row_id": i,
        "realm_id": i * 10,
        "event_id": i * 5,
    }
    for i in range(1, 4)
]


def generate_discussions_for_realmid(db: DiscussionDatabase, realm_id, discussions):
    for item in discussions:
        db.insert_discussion(realm_id, item["discussion"], item["input"], item["input_score"], item["ts"])


def format_discussions(discussions) -> list:
    INSERT_INDEX = 0
    res = []
    for item in discussions:
        res.insert(INSERT_INDEX, (item["discussion"], item["input"]))
    return res


def prepare_daily_discussion_tracker_data(db: DiscussionDatabase):
    for item in daily_discussion_tracker_data:
        db.insert_or_update_events_to_ignore_today(item["realm_id"], item["event_id"])


class ThoughtsDatabaseFiller:
    def __init__(self, database: DiscussionDatabase):
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
