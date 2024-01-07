import numpy as np
from pgvector.psycopg2 import register_vector
from utils import db_connect, create_embedding

# <-> L2 distance
# <#> Inner product
# <=> Cosine distance
# https://github.com/pgvector/pgvector

def get_top_discussions(mock_input, conn, limit):
    embedding_array = np.array(create_embedding(mock_input))
    # Register pgvector extension
    register_vector(conn)
    cur = conn.cursor()
    # Get the top 3 most similar documents using the KNN <=> operator
    cur.execute("SELECT content FROM embeddings ORDER BY embedding <=> %s LIMIT %s", embedding_array, limit)
    top_docs = cur.fetchall()
    return top_docs


mock_input = "test"

# Connect to PostgreSQL database
conn = db_connect("5430")
cur = conn.cursor()

print(get_top_discussions(input, conn), "3")