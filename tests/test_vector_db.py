import json

import pytest

from overlore.sqlite.vector_db import VectorDatabase


@pytest.mark.asyncio
async def test_insert():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = json.load(file)

    for row in mock_data:
        db.insert_townhall_discussion(
            row["discussion"], row["summary"], row["realmID"], json.dumps(row["event_id"]), row["embedding"]
        )

    rows, vss_rows = db.get_entries_count()

    assert rows == 6 and vss_rows == 6


# @pytest.mark.asyncio
# async def test_query_nearest_neighbour():
#     db = VectorDatabase.instance().init(":memory:")

#     with open("tests/data/embeddings.json") as file:
#         mock_data = json.load(file)

#     assert (0, 0) == db.get_entries_count()

#     with pytest.raises(ValueError) as exc_info:
#         db.query_nearest_neighbour(mock_data[0]["embedding"], 0, 0)
#     assert str(exc_info.value) == "Limit must be higher than 0"

#     with pytest.raises(ValueError) as exc_info:
#         db.query_nearest_neighbour(mock_data[0]["embedding"], 1, -1)
#     assert str(exc_info.value) == "Limit must be higher than 0"

#     assert [] == db.query_nearest_neighbour(mock_data[0]["embedding"], 1, 1)
#     assert [] == db.query_nearest_neighbour(mock_data[0]["embedding"], 100, 1)

#     for row in mock_data:
#         db.insert_townhall_discussion(
#             row["discussion"], row["summary"], row["realmID"], row["event_id"], row["embedding"]
#         )

#     assert (6, 6) == db.get_entries_count()
#     assert db.query_nearest_neighbour(mock_data[0]["embedding"], 1, 1)[0][0] == 2
#     assert [] == db.query_nearest_neighbour(mock_data[0]["embedding"], 100, 1)
#     assert db.query_nearest_neighbour(mock_data[0]["embedding"], 1, 2)[1][0] == 4

#     with pytest.raises(ValueError) as exc_info:
#         assert [] == db.query_nearest_neighbour(mock_data[0]["embedding"], 1, 0)
#     assert str(exc_info.value) == "Limit must be higher than 0"

#     with pytest.raises(ValueError) as exc_info:
#         db.query_nearest_neighbour(mock_data[0]["embedding"], 1, -1)
#     assert str(exc_info.value) == "Limit must be higher than 0"


# @pytest.mark.asyncio
# async def test_query_cosine_similarity():
#     db = VectorDatabase.instance().init(":memory:")

#     with open("tests/data/embeddings.json") as file:
#         mock_data = json.load(file)

#     assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 1)
#     assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 100)

#     for row in mock_data:
#         db.insert_townhall_discussion(
#             row["discussion"], row["summary"], row["realmID"], json.dumps(row["event_id"]), row["embedding"]
#         )

#     assert [(2, 0.9059480428695679)] == db.query_cosine_similarity(mock_data[0]["embedding"], 1)
#     assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 100, 1)

#     with pytest.raises(ValueError) as exc_info:
#         assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 1, 0)
#     assert str(exc_info.value) == "Limit must be higher than 0"

#     with pytest.raises(ValueError) as exc_info:
#         assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 1, -1)
#     assert str(exc_info.value) == "Limit must be higher than 0"
