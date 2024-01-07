from openai import OpenAI
import sqlite3
import sqlite_vss
import numpy as np
import struct
from typing import List
import json




mock_summary = """
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

mock_2 = "test"

def serialize(vector: List[float]) -> bytes:
  """ serializes a list of floats into a compact "raw bytes" format """
  return struct.pack('%sf' % len(vector), *vector)

def create_embedding(input, model="text-embedding-ada-002"):
    client = OpenAI()
    input = input.replace("\n", " ")
    return client.embeddings.create(input = [input], model=model).data[0].embedding

# Returns connection + cursor DB objects
def db_connect():
    conn = sqlite3.connect('test.db')
    conn.enable_load_extension(True)
    sqlite_vss.load(conn)
    conn.enable_load_extension(False)
    cur = conn.cursor()
    return conn, cur

def db_create():
    _, cur = db_connect()
    cur.execute("create table IF NOT EXISTS townhall (discussion text, embedding blob);")
    cur.execute("create virtual table IF NOT EXISTS vss_townhall using vss0(discussion(1000), embedding(1536));") # 1536 is the size of OPENAI embeddings


def db_insert(discussion, embedding):
    try:
        conn, cur = db_connect()
        binary_embedding = struct.pack(f'{len(embedding)}f', *embedding)
        cur.execute("INSERT INTO townhall(discussion, embedding) VALUES (?, ?);", (discussion, binary_embedding))
        print("Discussion inserted successfully.")

        # embedding_bytes = embedding.astype(np.float32).tobytes()
        # print(f"Embedding Type: {type(embedding_bytes)}, Length: {len(embedding_bytes)}")
        conn.commit()
        # cur.execute("INSERT INTO vss_townhall(embedding) VALUES (?);", [serialize(embedding)])
        cur.execute("INSERT INTO vss_townhall(rowid, discussion, embedding) select rowid, discussion, embedding from townhall;")
        # cur.execute("INSERT INTO vss_townhall(embedding) VALUES (?);", [embedding.astype(np.float32).tobytes()])

        
        print("Embedding inserted successfully.")
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Operational error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# def db_insert(discussion, embedding):
#     conn, cur = db_connect()
#     cur.execute("INSERT INTO townhall(discussion) VALUES (?);", (discussion,))
    # cur.execute("INSERT INTO vss_townhall(embedding) VALUES (?);", [embedding.astype(np.float32).tobytes()])
#     conn.commit()

def db_query(query_embedding):
    conn, cur = db_connect()
    # SQLite version 3.41+
    # cur.execute("""
    #     select rowid, distance from vss_townhall
    #     where vss_search(embedding, ?)
    #     limit 5
    # """, (query_embedding,))
    # results = cur.fetchall()
    # return results

    #SQLite version < 3.41
    cur.execute("""
        select rowid, distance from vss_townhall
        where vss_search(
            embedding,
            vss_search_params(
                ?,
                5
            )
        )
    """,  (query_embedding,))
    results = cur.fetchall()
    return results





def test_store(input):
    db_create()
    # db_insert(mock_2, np.array(create_embedding(mock_2)))
    # db_insert(mock_summary, np.array(create_embedding(mock_summary)))
    db_insert(input, create_embedding(input))

def test_retrieve():
    _, cur = db_connect()
    res = cur.execute("select embedding from vss_townhall where rowid=0;")
    emb = cur.fetchone()
    return emb[0]

    print(res.fetchall())
    print(res.rowcount)
    # print(res.  )
    return res


test_store("test1")
test_store("random2")
# print(test_retrieve())
# print(db_query(test_retrieve()))


# def testFunction():
#     conn = db_connect()
#     cur = conn.cursor()
#     cur.execute("""create table IF NOT EXISTS townhall (discussion text);""")
#     cur.execute("""create virtual table IF NOT EXISTS vss_townhall using vss0(embedding(1536));""")
    # cur.execute("CREATE VIRTUAL TABLE townhall using vss0(content TEXT, embedding(1536))")
#     res = cur.execute("""create virtual table test using vss0(
#   headline_embedding(384),
# );""")  

# testFunction()
    
# conn = db_connect()
# cur = conn.cursor()
# cur.execute("""
#     INSERT INTO townhall (discussion) VALUES ("test");
        
# """)

# conn.commit()