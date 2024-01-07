import sqlite3
import sqlite_vss
import numpy as np
from utils import create_embedding


# print(sqlite3.sqlite_version)
# print(sqlite_vss.vss_loadable_path())

# conn = sqlite3.connect('test.db')
# conn.enable_load_extension(True)
# sqlite_vss.load(conn)

# print(conn.execute('select vss_version()').fetchone()[0])

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

test = "test"



db = sqlite3.connect('test.db')
db.enable_load_extension(True)
sqlite_vss.load(db)
db.enable_load_extension(False)

version, = db.execute('select vss_version()').fetchone()
print(version)

# embedding = np.array([mock_discussion, create_embedding(mock_discussion)])

cur = db.cursor()

res = cur.execute("""create virtual table vss_xyz using vss0(
  headline_embedding(384),
);""")
print(res.fetchone())

# res = cur.execute("""create virtual table vss_xyz using vss0(
#   headline_embedding(384),
#   description_embedding(384) factory="IVF4096,Flat,IDMap2"
# );""")
# print(res.fetchone())

# embedding = np.array([create_embedding(test)])

# cur.execute(
#     "insert into vss_xyz values (?)", [embedding.astype(np.float32).tobytes()]
# )
# insert into vss_articles(rowid, headline_embedding)
#   select rowid, headline_embedding from articles;


# cur.execute("""
#     INSERT INTO vss_xyz VALUES
#         headline_embedding(384),
#         description_embedding(384)
# """)

db.commit()

res = cur.execute("SELECT COUNT(*) as cnt FROM vss_xyz;")
print(res.fetchall())

