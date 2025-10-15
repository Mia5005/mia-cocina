# backend/supabase_client.py
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "menu_images")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Define SUPABASE_URL y SUPABASE_KEY en .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------- MENU --------------------

def get_menu_remote():
    """Obtiene el menú completo desde Supabase"""
    resp = supabase.table("menu").select("*").execute()
    return resp.data or []

def upsert_menu_remote_by_nombre(item):
    """Inserta o actualiza un plato según su nombre"""
    nombre = item.get("nombre")
    if not nombre:
        return None
    existing = supabase.table("menu").select("*").eq("nombre", nombre).execute()
    data = {
        "nombre": nombre,
        "precio": item.get("precio", 0),
        "inventario": item.get("inventario", 0),
        "imagen": item.get("imagen")
    }
    if existing.data:
        rid = existing.data[0]["id"]
        supabase.table("menu").update(data).eq("id", rid).execute()
    else:
        supabase.table("menu").insert(data).execute()

# -------------------- PEDIDOS --------------------
def descontar_inventario(items):
    """Descuenta inventario del menú en Supabase según los items del pedido"""
    for it in items:
        try:
            menu_id = it.get("id")
            cantidad = it.get("cantidad", 0)
            if not menu_id or cantidad <= 0:
                continue
            # obtener inventario actual
            menu_row = supabase.table("menu").select("inventario").eq("id", menu_id).single().execute()
            if not menu_row.data:
                print(f"[WARN] No se encontró el plato con id={menu_id}")
                continue

            inventario_actual = int(menu_row.data["inventario"])
            nuevo_inventario = max(0, inventario_actual - cantidad)

            # actualizar inventario en la base remota
            supabase.table("menu").update({"inventario": nuevo_inventario}).eq("id", menu_id).execute()
            print(f"[INFO] Inventario actualizado: id={menu_id}, {inventario_actual} → {nuevo_inventario}")

        except Exception as e:
            print(f"[ERROR] al descontar inventario de {it}: {e}")

def insert_pedido_remote(mesa_id, total, items):
    """Crea un nuevo pedido remoto en Supabase"""
    timestamp = datetime.now().isoformat(timespec='seconds')
    data = {
        "mesa_id": mesa_id,
        "item": json.dumps(items),
        "total": total,
        "timestamp": timestamp,
        "finalizado": False
    }
    resp = supabase.table("pedidos").insert(data).execute()
    if resp.data and len(resp.data) > 0:
        # 👇 Descontar inventario inmediatamente después de guardar el pedido
        descontar_inventario(items)
        return resp.data[0]["id"]
    return None

def get_pedidos_remote():
    """Trae pedidos no finalizados"""
    resp = supabase.table("pedidos").select("*").eq("finalizado", False).execute()
    return resp.data or []

def get_pedidos_remote_all():
    """Trae todos los pedidos, incluidos los finalizados"""
    resp = supabase.table("pedidos").select("*").execute()
    return resp.data or []

def finalizar_pedido_remoto(pedido_id, estado: bool):
    """Actualiza el campo 'finalizado' de un pedido remoto"""
    supabase.table("pedidos").update({"finalizado": estado}).eq("id", pedido_id).execute()
    return True

# -------------------- STORAGE --------------------

def upload_image_to_storage(local_path, dest_filename):
    """Sube imagen al bucket y devuelve URL pública"""
    with open(local_path, "rb") as f:
        data = f.read()
    supabase.storage.from_(SUPABASE_BUCKET).upload(dest_filename, data, {"upsert": True})
    public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(dest_filename)
    return public_url.get("publicURL") if isinstance(public_url, dict) else public_url
