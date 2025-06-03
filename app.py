from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import json
import os

app = Flask(__name__)
CORS(app)

DB_FILE = "cuentas.json"

# 📥 Leer datos desde JSON
def cargar_cuentas():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 💾 Guardar datos en JSON
def guardar_cuentas(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# 🔄 Regenerar regalos individuales por cuenta
def actualizar_regalos(cuentas):
    tiempo_actual = time.time()
    cambios = False

    for cuenta in cuentas:
        tiempos = cuenta.get("regalos_tiempos", [])
        # Limpiar tiempos expirados
        nuevos_tiempos = [t for t in tiempos if t > tiempo_actual - 86400]
        if len(nuevos_tiempos) < len(tiempos):
            cambios = True
        cuenta["regalos_tiempos"] = nuevos_tiempos
        cuenta["regalos_disponibles"] = max(0, 5 - len(nuevos_tiempos))

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
        "regalos_tiempos": []
    }
    cuentas.append(nueva)
    guardar_cuentas(cuentas)
    return jsonify(nueva), 201

# ✏️ Actualizar cuenta
@app.route("/api/cuentas/<int:id>", methods=["PUT"])
def actualizar_cuenta(id):
    data = request.json
    cuentas = cargar_cuentas()

    for cuenta in cuentas:
        if cuenta["id"] == id:
            # Campos simples
            for key in ["nombre", "pavos"]:
                if key in data:
                    cuenta[key] = data[key]

            # Control de regalos
            if "regalos_disponibles" in data:
                actual = cuenta.get("regalos_disponibles", 5)
                nuevo = data["regalos_disponibles"]

                if nuevo < actual:
                    # Registrar un nuevo envío solo si es decremento
                    cuenta.setdefault("regalos_tiempos", []).append(time.time())
                elif nuevo > actual:
                    # Permitir reinicio manual
                    cuenta["regalos_tiempos"] = []

                cuenta["regalos_disponibles"] = nuevo

            guardar_cuentas(cuentas)
            return jsonify(cuenta)

    return jsonify({"error": "Cuenta no encontrada"}), 404

# 🗑️ Eliminar cuenta
@app.route("/api/cuentas/<int:id>", methods=["DELETE"])
def eliminar_cuenta(id):
    cuentas = cargar_cuentas()
    nuevas = [c for c in cuentas if c["id"] != id]
    if len(nuevas) != len(cuentas):
        guardar_cuentas(nuevas)
        return jsonify({"mensaje": "Cuenta eliminada"}), 200
    return jsonify({"error": "Cuenta no encontrada"}), 404

# 🚀 Iniciar servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
