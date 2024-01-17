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
        db.mock_insert(row)

    rows, vss_rows = db.get_all()

    assert rows == 6 and vss_rows == 6


@pytest.mark.asyncio
async def test_query_nearest_neighbour():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = (json.load(file))[2]

    for row in mock_data:
        db.mock_insert(row)

    rows, vss_rows = db.get_all()

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
        db.mock_insert(row)

    with open("tests/data/embeddings.json") as file:
        query_data = (json.load(file))[1]

    res = db.query_cosine_similarity(query_data[0]["embedding"])
    assert res[0][0] == 1


@pytest.mark.asyncio
async def test_query_event_id():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = (json.load(file))[2]

    for row in mock_data:
        db.mock_insert(row)

    res = db.query_event_ids(5)

    res = db.query_event_ids(10)
    assert res == (10, False)
