import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "cocinamia.db"
if not DB.exists():
    print("La base de datos no existe:", DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()

def show_table(name, limit=5):
    print(f"\n== {name} ==")
    try:
        cur.execute(f"SELECT COUNT(*) FROM {name}")
        print('count:', cur.fetchone()[0])
        cur.execute(f"SELECT * FROM {name} LIMIT ?", (limit,))
        rows = cur.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print('error:', e)

for t in ['menu', 'pedidos', 'pedido_items']:
    show_table(t)

conn.close()
