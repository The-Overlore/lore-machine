import json

import pytest

from overlore.db.vector_db_handler import VectorDatabaseHandler


@pytest.mark.asyncio
async def test_vss_version():
    db = VectorDatabaseHandler.instance().init(":memory:")

    vss_version = db.vss_version()
    assert vss_version == "v0.1.2"


@pytest.mark.asyncio
async def test_insert():
    db = VectorDatabaseHandler.instance().init(":memory:")

    with open("tests/data/embeddings/skewed_emb.json") as file:
        mock_data = json.load(file)

    for row in mock_data:
        db.mock_insert(row)

    rows, vss_rows = db.get_all()

    assert rows == 6 and vss_rows == 6


@pytest.mark.asyncio
async def test_query_nearest_neighbour():
    db = VectorDatabaseHandler.instance().init(":memory:")

    with open("tests/data/embeddings/skewed_emb.json") as file:
        mock_data = json.load(file)

    for row in mock_data:
        db.mock_insert(row)

    with open("tests/data/embeddings/query_embeddings.json") as file:
        query_data = json.load(file)

    for row in query_data:
        res = db.query_nn(row["embedding"], 1)
    print(res)

    assert res[0][0] == 5


# @pytest.mark.asyncio
# async def test_query_cosine_similarity():
#     db = VectorDatabaseHandler.instance().init(":memory:")

#     with open("tests/data/embeddings/skewed_emb.json") as file:
#         mock_data = json.load(file)

#     for row in mock_data:
#         db.mock_insert(row)

#     with open("tests/data/embeddings/query_embeddings.json") as file:
#         query_data = json.load(file)

#     res = []
#     for row in query_data:
#         res.append(db.query_cosine_similarity(row["embedding"]))
#     output = find_closest_to_one(res)

#     assert output == 2


@pytest.mark.asyncio
async def test_query_event_id():
    db = VectorDatabaseHandler.instance().init(":memory:")

    with open("tests/data/embeddings/skewed_emb.json") as file:
        mock_data = json.load(file)

    for row in mock_data:
        db.mock_insert(row)

    res = db.query_event_ids(5)

    res = db.query_event_ids(10)
    assert res == (10, False)
