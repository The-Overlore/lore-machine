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

    with open("data/embeddings/summary_embeddings.json") as file:
        mock_data = json.load(file)

    for row in mock_data:
        db.mock_insert(row)

    rows, vss_rows = db.get_all()

    assert rows == 7 and vss_rows == 7


@pytest.mark.asyncio
async def test_query_nearest_neighbour():
    db = VectorDatabaseHandler.instance().init(":memory:")

    with open("data/embeddings/skewed_emb.json") as file:
        mock_data = json.load(file)

    for row in mock_data:
        db.mock_insert(row)

    with open("data/embeddings/query_embeddings.json") as file:
        query_data = json.load(file)

    for row in query_data:
        res = db.query_nn(row["embedding"], 1)
    print(res)

    assert res[0][0] == 1


@pytest.mark.asyncio
async def test_query_cosine_similarity():
    db = VectorDatabaseHandler.instance().init(":memory:")

    with open("data/embeddings/skewed_emb.json") as file:
        mock_data = json.load(file)

    for row in mock_data:
        db.mock_insert(row)

    with open("data/embeddings/query_embeddings.json") as file:
        query_data = json.load(file)

    for row in query_data:
        res = db.query_cosine_similarity(row["embedding"])
        output = db.find_closest_to_one(res)
        # print(output)

    assert output == 2


# TEST W/ ACTUAL API CALLS
# Use db.insert() for OPENAI embeddings generator implementation
# for input in input_list:
#     db.insert(input)

# TEST W/ MOCK DATA (Uses OPENAI generated embeddings)

# with open("data/embeddings/summary_embeddings.json") as file:
#     mock_data = json.load(file)

# # Insert each JSON object into the database
# for row in mock_data:
#     db.mock_insert(row)

# # Prints database rows (embeddings are shortened)
# db.get_all()

# with open("data/embeddings/query_embeddings.json") as file:
#     query_data = json.load(file)

# print("\n QUERIES \n")
# # Nearest neighbor
# # for row in query_data:
# #     res = db.query_nn(row["embedding"])
# #     print(res)

# # Cosine similarity
# for row in query_data:
#     res = db.query_cosine_similarity(row["embedding"])
#     # print(res[0][0])
#     output = db.find_lowest_second_param(res)
#     print(output)

# assert 1 == 2
