test_data = [
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


def prepare_data(db):
    for item in test_data:
        db.insert_npc_profile(item["realm_entity_id"], item["profile"])
