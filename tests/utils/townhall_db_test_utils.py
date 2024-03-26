given_townhall_values = [
    {"rowid": i, "discussion": f"Discussion {i}", "input": f"Input {i}", "realm_id": i * 100} for i in range(1, 4)
]

given_townhall_values_for_single_realm = [
    {
        "discussion": f"Discussion {i}",
        "input": f"Input {i}",
    }
    for i in range(1, 4)
]

given_plots = [{"rowid": i, "realm_id": i, "plot": f"plot {i}"} for i in range(1, 4)]

given_update_plots = [{"rowid": i, "realm_id": i, "new_plot": f"new plot {i}"} for i in range(1, 4)]

given_thoughts = [
    {"rowid": i, "npc_entity_id": i * 100, "thought": f"Thought {i}", "embedding": [0.1]} for i in range(1, 4)
]


def generate_townhalls_for_realmid(db, realm_id, townhalls):
    for item in townhalls:
        db.insert_townhall_discussion(realm_id, item["discussion"], item["input"])


def generate_plotlines(db):
    for item in given_plots:
        db.insert_plotline(item["realm_id"], "plot")


def format_townhalls(townhalls) -> list:
    res = []
    for item in townhalls:
        res.append((item["discussion"], item["input"]))
    return res
