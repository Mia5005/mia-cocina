# app.py
import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps 
from backend.supabase_client import (
    get_menu_remote,
    upsert_menu_remote_by_nombre,
    insert_pedido_remote,
    upload_image_to_storage,
    get_pedidos_remote,
    finalizar_pedido_remoto,
    get_pedidos_remote_all,
    
)
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key") # cámbiala por una variable segura

#----------------- DECORADO -----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function
# ------------------ LOGIN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        valid_user = os.getenv("ADMIN_USER")
        valid_password = os.getenv("ADMIN_PASSWORD")

        if user == valid_user and password == valid_password:
            session["user"] = user
            return redirect(url_for("panel"))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@app.route("/panel")
@login_required
def panel():
    return render_template("panel.html", user=session["user"])

# ------------------ RUTAS ------------------

@app.route("/")
def index():
    menu = get_menu_remote()
    print("Menu loaded:", menu)
    return render_template("index.html", menu=menu)
@app.route("/pedido", methods=["POST"])
def crear_pedido():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se envió JSON válido"}), 400

        mesa_id = data.get("mesa_id", "SinMesa")
        items = data.get("items", [])
        if not items:
            return jsonify({"status": "error", "message": "No hay items"}), 400

        total = sum(i["precio"] * i["cantidad"] for i in items)
        pid = insert_pedido_remote(mesa_id, total, items)

        return jsonify({
            "status": "ok",
            "message": f"Pedido guardado correctamente (ID {pid})",
            "pedido_id": pid
        }), 200

    except Exception as e:
        print("Error al crear pedido:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/cocina")
@login_required
def cocina():
    pedidos = get_pedidos_remote()

    # 🔧 Convertir 'item' de texto JSON a lista real
    for p in pedidos:
        if isinstance(p.get("item"), str):
            try:
                p["item"] = json.loads(p["item"])
            except Exception as e:
                print("Error al decodificar item:", e)
                p["item"] = []
        elif not isinstance(p.get("item"), list):
            p["item"] = []

    return render_template("cocina.html", pedidos=pedidos)


@app.route("/cocina/finalizar/<int:pedido_id>", methods=["POST"])
def finalizar_pedido(pedido_id):
    try:
        finalizar_pedido_remoto(pedido_id, True)
        return jsonify({
            "status": "ok",
            "message": f"Pedido {pedido_id} finalizado correctamente."
        })
    except Exception as e:
        print("Error finalizando pedido:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/historial")
def historial():
    historial = get_pedidos_remote_all()
    return render_template("historial.html", historial=historial)

# ---------------- ADMIN ----------------
@app.route("/admin")
@login_required
def admin():
    # 🔹 Obtener datos remotos
    menu = get_menu_remote()
    pedidos = get_pedidos_remote()

    # 🔧 Convertir 'item' de string JSON a lista real
    for p in pedidos:
        if isinstance(p.get("item"), str):
            try:
                p["item"] = json.loads(p["item"])
            except Exception as e:
                print("Error al decodificar item en admin:", e)
                p["item"] = []
        elif not isinstance(p.get("item"), list):
            p["item"] = []

    # 🔹 Obtener historial completo (finalizados)
    historial = get_pedidos_remote_all()

    print("Pedidos procesados para admin:", pedidos)
    return render_template("admin.html", menu=menu, pedidos=pedidos, historial=historial)


@app.route("/admin/actualizar", methods=["POST"])
def admin_actualizar():
    data = request.get_json()
    try:
        upsert_menu_remote_by_nombre(data)
        return jsonify({"status": "ok", "message": "Plato actualizado en Supabase."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/admin/subir_imagen/<string:nombre>", methods=["POST"])
def admin_subir_imagen(nombre):
    file = request.files.get("imagen")
    if not file:
        return jsonify({"status": "error", "message": "No file sent"}), 400

    filename = file.filename
    tmp_path = os.path.join("static", "images")
    os.makedirs(tmp_path, exist_ok=True)
    local_path = os.path.join(tmp_path, filename)
    file.save(local_path)

    try:
        public_url = upload_image_to_storage(local_path, f"menu/{filename}")
        upsert_menu_remote_by_nombre({
            "nombre": nombre,
            "imagen": public_url
        })
        return jsonify({
            "status": "ok",
            "message": "Imagen subida y sincronizada.",
            "url": public_url
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

