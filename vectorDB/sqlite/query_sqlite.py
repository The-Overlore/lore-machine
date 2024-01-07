import sqlite3
import sqlite_vss

db = sqlite3.connect('test.db')
db.enable_load_extension(True)
sqlite_vss.load(db)
# Why false again ??
db.enable_load_extension(False)

cur = db.cursor()

# NN search (vss_search). How to use other type ?? + wtf syntax ??
res = cur.execute("""select *
from vss_xyz
where vss_search(
  headline_embedding,
  (select headline_embedding from articles where rowid = 123)
)
limit 3;""")
print(res.fetchall())