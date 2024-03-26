given_insert_values = [
    {
        "realm_entity_id": i,
        "npc_entity_id": i * 100,
        "profile": {
            "full_name": f"fullname {i}",
            "characteristics": {"age": i, "sex": i, "role": i},
            "character_trait": f"trait {i}",
            "description": f"description {i}",
        },
        "rowid": i,
    }
    for i in range(1, 4)
]


def insert_data_into_db(db):
    for item in given_insert_values:
        db.insert_npc_spawn(item["realm_entity_id"], item["profile"])
