# backend/database.py
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cocinamia.db")
DB_PATH = os.path.abspath(DB_PATH)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL,
        inventario INTEGER DEFAULT 0,
        imagen TEXT
    );

    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa_id TEXT,
        items TEXT,
        total REAL,
        timestamp TEXT,
        finalizado INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa_id TEXT,
        items TEXT,
        total REAL,
        timestamp TEXT
    );
    """)
    conn.commit()
    conn.close()

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- MENU ---
def get_menu_local():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM menu ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_menu_item_by_nombre(nombre):
    conn = get_conn()
    r = conn.execute("SELECT * FROM menu WHERE nombre = ?", (nombre,)).fetchone()
    conn.close()
    return dict(r) if r else None

def upsert_menu_local(nombre, precio, inventario, imagen=None):
    # If exists by nombre update, else insert
    existing = get_menu_item_by_nombre(nombre)
    conn = get_conn()
    if existing:
        conn.execute("UPDATE menu SET precio=?, inventario=?, imagen=? WHERE nombre=?",
                     (precio, inventario, imagen, nombre))
    else:
        conn.execute("INSERT INTO menu (nombre, precio, inventario, imagen) VALUES (?, ?, ?, ?)",
                     (nombre, precio, inventario, imagen))
    conn.commit()
    conn.close()

def update_menu_by_id_local(id_, nombre, precio, inventario, imagen=None):
    conn = get_conn()
    conn.execute("UPDATE menu SET nombre=?, precio=?, inventario=?, imagen=? WHERE id=?",
                 (nombre, precio, inventario, imagen, id_))
    conn.commit()
    conn.close()

def insert_menu_local(nombre, precio, inventario, imagen=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO menu (nombre, precio, inventario, imagen) VALUES (?, ?, ?, ?)",
                (nombre, precio, inventario, imagen))
    conn.commit()
    last = cur.lastrowid
    conn.close()
    return last

# --- PEDIDOS ---
def insert_pedido_local(mesa_id, items, total):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO pedidos (mesa_id, items, total, timestamp, finalizado) VALUES (?, ?, ?, ?, ?)",
                (mesa_id, json.dumps(items, ensure_ascii=False), total, datetime.now().isoformat(timespec="seconds"), 0))
    conn.commit()
    last = cur.lastrowid
    conn.close()
    return last

def get_pedidos_local(finalizado=0):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM pedidos WHERE finalizado = ? ORDER BY id DESC", (1 if finalizado else 0,)).fetchall()
    conn.close()
    res = [dict(r) for r in rows]
    for r in res:
        r["items"] = json.loads(r["items"]) if r["items"] else []
    return res

def finalizar_pedido_local(pedido_id):
    conn = get_conn()
    # move to historial
    r = conn.execute("SELECT * FROM pedidos WHERE id=?", (pedido_id,)).fetchone()
    if not r:
        conn.close()
        return False
    conn.execute("INSERT INTO historial (mesa_id, items, total, timestamp) VALUES (?, ?, ?, ?)",
                 (r["mesa_id"], r["items"], r["total"], datetime.now().isoformat(timespec="seconds")))
    conn.execute("UPDATE pedidos SET finalizado=1 WHERE id=?", (pedido_id,))
    conn.commit()
    conn.close()
    return True

def get_historial_local():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM historial ORDER BY id DESC").fetchall()
    conn.close()
    res = [dict(r) for r in rows]
    for r in res:
        r["items"] = json.loads(r["items"]) if r["items"] else []
    return res

def clear_historial_local():
    conn = get_conn()
    conn.execute("DELETE FROM historial")
    conn.execute("DELETE FROM pedidos WHERE finalizado = 1")
    conn.commit()
    conn.close()
