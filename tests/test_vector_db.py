import json

import pytest

from overlore.sqlite.vector_db import VectorDatabase

# data/embeddings.json structure:
# 0. townhall discussions embeddings
# 1. query embedding
# 2. skewed embeddings
# 3. summary embeddings


@pytest.mark.asyncio
async def test_insert():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = (json.load(file))[2]

    for row in mock_data:
        db.insert_townhall_discussion(
            row["discussion"], row["realmID"], json.dumps(row["events_ids"]), row["embedding"]
        )

    rows, vss_rows = db.get_entries_count()

    assert rows == 6 and vss_rows == 6


@pytest.mark.asyncio
async def test_query_nearest_neighbour():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = (json.load(file))[2]

    for row in mock_data:
        db.insert_townhall_discussion(
            row["discussion"], row["realmID"], json.dumps(row["events_ids"]), row["embedding"]
        )

    rows, vss_rows = db.get_entries_count()

    assert rows == 6 and vss_rows == 6

    with open("tests/data/embeddings.json") as file:
        query_data = (json.load(file))[1]

    res = db.query_nearest_neighbour(query_data[0]["embedding"], 1, 1)
    assert res[0][0] == 5


@pytest.mark.asyncio
async def test_query_cosine_similarity():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = (json.load(file))[2]

    for row in mock_data:
        db.insert_townhall_discussion(
            row["discussion"], row["realmID"], json.dumps(row["events_ids"]), row["embedding"]
        )

    with open("tests/data/embeddings.json") as file:
        query_data = (json.load(file))[1]

    res = db.query_cosine_similarity(query_data[0]["embedding"])
    assert res[0][0] == 1


@pytest.mark.asyncio
async def test_get_townhalls_from_events():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = (json.load(file))[2]

    for row in mock_data:
        db.insert_townhall_discussion(row["discussion"], row["realmID"], row["events_ids"], row["embedding"])

    event_ids = [5, 3, 2, 1, 8]
    res = db.get_townhalls_from_events(event_ids)
    expected = (
        [
            "Nancy: The fields whisper tales of our victory, but what worth is gold if our stomachs echo with"
            " emptiness?\n    James: That's just it, isn't it? We've struck the earth till our hands bled, only to"
            " trade our fish for a pitiful sum of gold. Fools' math!\n    Lisa: Let peace fill your hearts, friends. We"
            " grieve for the fallen, yet our defenses still stand. There is hope in our unity.\n    Daniel: Hope? Speak"
            " not to me of hope when swords clash outside our doors. We must fortify, prepare! Besides, the mines won't"
            " shield us nor fill our plates.\n    Paul: Our plows lay idle and our nets gather dust. What good is coin"
            " when the wheat does not sway and the fish leap away from our grasp?\n    James: Rage swells within! What"
            " good is a war won when our own people lie dead? Tell me that, friends! Tell me!\n    Nancy: Listen to the"
            " wind, for it carries both the songs of triumph and the cries of the hungry. Victory is a fickle"
            " mistress.\n    Lisa: Peace, James. Let not anger cloud our judgment. The earth has riches yet to yield,"
            " and the seas will provide. We must toil together.\n    Daniel: Toil, you say! It's time to wield the"
            " pickaxe as a spear if need be. Our brethren were not lost to toil, but to bloodshed.\n    Paul: Aye, it's"
            " the toil that's forgotten once the blood dries. Perhaps the lesson here lies not in the clashing of"
            " swords but in the joining of hands.\n    Nancy: With a bounty of gold and an ache in our bellies, we"
            " stand at a crossroads. Shall we eat or shall we arm? That is the question, and the crops won't wait."
        ],
        [],
    )
    assert res == expected
