import sqlite3

DB_PATH = "cocinamia.db"

# Conectarse y crear tablas
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Tabla de pedidos
cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mesa_id TEXT NOT NULL,
    total REAL NOT NULL,
    timestamp TEXT NOT NULL,
    finalizado INTEGER DEFAULT 0
)
""")

# Tabla de items de pedido
cursor.execute("""
CREATE TABLE IF NOT EXISTS pedido_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER,
    nombre TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio REAL NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
)
""")

conn.commit()
conn.close()
print("✅ Base de datos cocinamia.db creada correctamente.")


