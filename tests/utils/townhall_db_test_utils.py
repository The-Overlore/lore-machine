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
    {"rowid": i, "npc_entity_id": i * 100, "thought": f"Thought {i}", "poignancy": i, "embedding": [0.1]}
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
