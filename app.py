from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import json
import os

app = Flask(__name__)
CORS(app)

DB_FILE = "cuentas.json"

# 📥 Cargar cuentas desde archivo JSON
def cargar_cuentas():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 💾 Guardar cuentas en archivo JSON
def guardar_cuentas(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# 🔄 Regenerar regalos cada 24h (máximo 5)
def actualizar_regalos(cuentas):
    tiempo_actual = time.time()
    cambios = False
    for cuenta in cuentas:
        while cuenta["regalos_disponibles"] < 5 and tiempo_actual - cuenta["ultimo_regalo"] >= 86400:
            cuenta["regalos_disponibles"] += 1
            cuenta["ultimo_regalo"] += 86400
            cambios = True
    return cambios

# ✅ Obtener todas las cuentas
@app.route("/api/cuentas", methods=["GET"])
def obtener_cuentas():
    cuentas = cargar_cuentas()
    if actualizar_regalos(cuentas):
        guardar_cuentas(cuentas)
    return jsonify(cuentas)

# ➕ Agregar nueva cuenta
@app.route("/api/cuentas", methods=["POST"])
def agregar_cuenta():
    data = request.json
    cuentas = cargar_cuentas()
    nueva = {
        "id": int(time.time() * 1000),
        "nombre": data.get("nombre", "SinNombre"),
        "pavos": data.get("pavos", 0),
        "regalos_disponibles": 5,
        "ultimo_regalo": time.time()
    }
    cuentas.append(nueva)
    guardar_cuentas(cuentas)
    return jsonify(nueva), 201

# ✏️ Actualizar cuenta por ID (nombre, pavos, regalos_disponibles, ultimo_regalo)
@app.route("/api/cuentas/<int:id>", methods=["PUT"])
def actualizar_cuenta(id):
    data = request.json
    cuentas = cargar_cuentas()
    for cuenta in cuentas:
        if cuenta["id"] == id:
            # Solo actualiza los campos válidos
            for key in ["nombre", "pavos", "regalos_disponibles", "ultimo_regalo"]:
                if key in data:
                    cuenta[key] = data[key]
            guardar_cuentas(cuentas)
            return jsonify(cuenta)
    return jsonify({"error": "Cuenta no encontrada"}), 404

# 🗑️ Eliminar cuenta por ID
@app.route("/api/cuentas/<int:id>", methods=["DELETE"])
def eliminar_cuenta(id):
    cuentas = cargar_cuentas()
    cuentas_filtradas = [c for c in cuentas if c["id"] != id]
    if len(cuentas_filtradas) != len(cuentas):
        guardar_cuentas(cuentas_filtradas)
        return jsonify({"mensaje": "Cuenta eliminada"}), 200
    return jsonify({"error": "Cuenta no encontrada"}), 404

# 🚀 Ejecutar servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
