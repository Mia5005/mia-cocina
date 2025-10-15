import sqlite3
from pathlib import Path
DB = Path(__file__).parent / 'cocinamia.db'
print('DB path:', DB.resolve())
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('tables:', cur.fetchall())
conn.close()
