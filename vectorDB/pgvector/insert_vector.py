from pgvector.psycopg2 import register_vector
from psycopg2.extras import execute_values
import numpy as np
from utils import db_connect, create_embedding

#First, run export OPENAI_API_KEY=sk-YOUR_OPENAI_API_KEY...
# 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

def check_table_exists(cur, table_name):
    cur.execute(f"SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '{table_name}');")
    return cur.fetchone()[0]

mock_discussion = """
In "Eternum," a community dialogue unfolds concerning the recent victory at war that cost the lives of 102 soldiers 
and an ongoing crisis of food scarcity despite the happy state of the realm. 
Nancy, James, Lisa, Daniel, and Paul express a spectrum of emotions from happiness and euphoria to agitation and rage. 
They debate the value of the war's loot against the immediate need for food and the persistent threat to their defenses. 
Nancy highlights the paradox of wealth amidst hunger, 
while James fumes over the casualties and poor trade-off from their latest transaction. 
Lisa preaches unity and resiliency whereas Daniel stresses the necessity of a defensive stance and 
Paul adds that cooperation is key in overcoming their hardships. 
The conversation reveals a community grappling with the tension between survival and security, 
with an undercurrent suggesting the potential for greater collaboration to address their challenges.
"""

# Connect to PostgreSQL database
conn = db_connect("5430")
cur = conn.cursor()

# Check if the 'embeddings' table already exists
if not check_table_exists(conn, cur, 'embeddings'):

    #install pgvector
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()

    # Register the vector type with psycopg2
    register_vector(conn)

    table_create_command = """
    CREATE TABLE embeddings (
                id bigserial primary key,
                content text,
                embedding vector(1536)
                );
    """

    cur.execute(table_create_command)
    cur.close()
    conn.commit()

#Batch insert embeddings and metadata from dataframe into PostgreSQL database
register_vector(conn)
cur = conn.cursor()

# Prepare the list of tuples to insert
data = [(mock_discussion, np.array(create_embedding(mock_discussion)))]
# Use execute_values to perform batch insertion !! SLOW, PROB USE SMTH ELSE !!
execute_values(cur, "INSERT INTO embeddings (content, embedding) VALUES %s", data)
# Commit after we insert all embeddings
conn.commit()


# Sanity checks

cur.execute("SELECT COUNT(*) as cnt FROM embeddings;")
num_records = cur.fetchone()[0]
print("Number of vector records in table: ", num_records,"\n")

# print the first record in the table, for sanity-checking
cur.execute("SELECT * FROM embeddings LIMIT 1;")
records = cur.fetchall()
print("First record in table: ", records)

