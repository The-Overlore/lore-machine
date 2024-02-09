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
            row["discussion"], row["summary"], row["realmID"], json.dumps(row["events_ids"]), row["embedding"]
        )

    rows, vss_rows = db.get_entries_count()

    assert rows == 6 and vss_rows == 6


@pytest.mark.asyncio
async def test_query_nearest_neighbour():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = json.load(file)

    assert (0, 0) == db.get_entries_count()

    with pytest.raises(RuntimeError) as exc_info:
        db.query_nearest_neighbour(mock_data[0]["embedding"], 0, 0)
    assert str(exc_info.value) == "Empty vector db"

    with pytest.raises(RuntimeError) as exc_info:
        db.query_nearest_neighbour(mock_data[0]["embedding"], 1, 1)
    assert str(exc_info.value) == "Empty vector db"

    with pytest.raises(RuntimeError) as exc_info:
        db.query_nearest_neighbour(mock_data[0]["embedding"], 100, 1)
    assert str(exc_info.value) == "Empty vector db"

    with pytest.raises(RuntimeError) as exc_info:
        db.query_nearest_neighbour(mock_data[0]["embedding"], 1, -1)
    assert str(exc_info.value) == "Empty vector db"

    for row in mock_data:
        db.insert_townhall_discussion(
            row["discussion"], row["summary"], row["realmID"], row["events_ids"], row["embedding"]
        )

    assert (6, 6) == db.get_entries_count()
    assert db.query_nearest_neighbour(mock_data[0]["embedding"], 1, 1)[0][0] == 2
    assert [] == db.query_nearest_neighbour(mock_data[0]["embedding"], 100, 1)
    assert db.query_nearest_neighbour(mock_data[0]["embedding"], 1, 2)[1][0] == 4

    with pytest.raises(ValueError) as exc_info:
        assert [] == db.query_nearest_neighbour(mock_data[0]["embedding"], 1, 0)
    assert str(exc_info.value) == "Limit must be higher than 0"

    with pytest.raises(ValueError) as exc_info:
        db.query_nearest_neighbour(mock_data[0]["embedding"], 1, -1)
    assert str(exc_info.value) == "Limit must be higher than 0"


@pytest.mark.asyncio
async def test_query_cosine_similarity():
    db = VectorDatabase.instance().init(":memory:")

    with open("tests/data/embeddings.json") as file:
        mock_data = json.load(file)

    assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 1)
    assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 100)

    for row in mock_data:
        db.insert_townhall_discussion(
            row["discussion"], row["summary"], row["realmID"], json.dumps(row["events_ids"]), row["embedding"]
        )

    assert [(2, 0.9059480428695679)] == db.query_cosine_similarity(mock_data[0]["embedding"], 1)
    assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 100, 1)

    with pytest.raises(ValueError) as exc_info:
        assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 1, 0)
    assert str(exc_info.value) == "Limit must be higher than 0"

    with pytest.raises(ValueError) as exc_info:
        assert [] == db.query_cosine_similarity(mock_data[0]["embedding"], 1, -1)
    assert str(exc_info.value) == "Limit must be higher than 0"


@pytest.mark.asyncio
async def test_get_townhalls_from_events():
    vec_db = VectorDatabase.instance().init(":memory:")

    assert (0, 0) == vec_db.get_entries_count()

    mock_event_ids = []
    assert ([], []) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [1]
    assert ([], [1]) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [1, 2]
    assert ([], [1, 2]) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [1, 2, 3]
    assert ([], [1, 2, 3]) == vec_db.get_townhalls_from_events(mock_event_ids)

    with open("tests/data/embeddings.json") as file:
        mock_data = json.load(file)

    for row in mock_data:
        vec_db.insert_townhall_discussion(
            row["discussion"], row["summary"], row["realmID"], row["events_ids"], row["embedding"]
        )
    assert (6, 6) == vec_db.get_entries_count()

    mock_event_ids = []
    assert ([], []) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [1]
    assert (["1 the villagers are mad and grumpy"], []) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [1, 2]
    assert (["1 the villagers are mad and grumpy"], []) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [1, 2, 3]
    assert (["1 the villagers are mad and grumpy"], []) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [100]
    assert ([], [100]) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [7, 100]
    assert (["2 the villagers are mad and grumpy"], [100]) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [100, 101, 102]
    assert ([], [100, 101, 102]) == vec_db.get_townhalls_from_events(mock_event_ids)

    mock_event_ids = [7, 8, 9, 10, 11, 12]
    assert vec_db.get_townhalls_from_events(mock_event_ids) == (
        [
            "1 the villagers are mad and grumpy",
            "2 the villagers are mad and grumpy",
            "3 the villagers are mad and grumpy",
            "4 the villagers are mad and grumpy",
            "5 the villagers are mad and grumpy",
            "6 the villagers are mad and grumpy",
        ],
        [],
    )
