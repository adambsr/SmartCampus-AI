import os, sys, psycopg
from dotenv import load_dotenv

load_dotenv()
sql = open(sys.argv[1], encoding="utf-8").read()
with psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True) as conn:
    conn.execute(sql)
    rows = conn.execute("select table_name from information_schema.tables where table_schema = 'public' order by 1").fetchall()
print(len(rows), "tables:", [r[0] for r in rows])
