"""
app/api.py
La API: un servidor que escucha peticiones por la red, para que las
tabletas (y cualquier navegador) puedan ver y agregar datos del menú.
Usa la MISMA base de datos que la app de escritorio.
"""

import socket
import sqlite3
from flask import Flask, jsonify, request, g

from app.basedatos import obtener_conexion, crear_tablas

app = Flask(__name__)


def db():
    if "conexion" not in g:
        g.conexion = obtener_conexion()
    return g.conexion


@app.teardown_appcontext
def cerrar_conexion(excepcion=None):
    conexion = g.pop("conexion", None)
    if conexion is not None:
        conexion.close()


@app.get("/salud")
def salud():
    return jsonify({"ok": True})


@app.get("/api/categorias")
def listar_categorias():
    filas = db().execute("SELECT * FROM categorias ORDER BY orden, nombre").fetchall()
    return jsonify([dict(f) for f in filas])


@app.post("/api/categorias")
def crear_categoria():
    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")
    orden = datos.get("orden", 0)

    if not nombre or not isinstance(nombre, str):
        return jsonify({"error": "Falta el nombre"}), 400

    try:
        cursor = db().execute(
            "INSERT INTO categorias (nombre, orden) VALUES (?, ?)", (nombre, orden)
        )
        db().commit()
    except sqlite3.IntegrityError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"id": cursor.lastrowid, "nombre": nombre, "orden": orden}), 201


@app.get("/api/productos")
def listar_productos():
    filas = db().execute(
        """
        SELECT p.id, p.nombre, p.precio_centavos, p.disponible, c.nombre AS categoria
        FROM productos p JOIN categorias c ON c.id = p.categoria_id
        ORDER BY c.orden, p.nombre
        """
    ).fetchall()
    return jsonify([dict(f) for f in filas])


@app.post("/api/productos")
def crear_producto():
    datos = request.get_json(silent=True) or {}
    categoria_id = datos.get("categoria_id")
    nombre = datos.get("nombre")
    precio_centavos = datos.get("precio_centavos")

    if not categoria_id or not nombre or not isinstance(precio_centavos, int):
        return jsonify({
            "error": "Se necesita categoria_id, nombre y precio_centavos (número entero)"
        }), 400

    try:
        cursor = db().execute(
            "INSERT INTO productos (categoria_id, nombre, precio_centavos) VALUES (?, ?, ?)",
            (categoria_id, nombre, precio_centavos),
        )
        db().commit()
    except sqlite3.IntegrityError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"id": cursor.lastrowid, "nombre": nombre, "precio_centavos": precio_centavos}), 201


@app.get("/api/mesas")
def listar_mesas():
    filas = db().execute("SELECT * FROM mesas ORDER BY numero").fetchall()
    return jsonify([dict(f) for f in filas])


@app.post("/api/mesas")
def crear_mesa():
    datos = request.get_json(silent=True) or {}
    numero = datos.get("numero")

    if not isinstance(numero, int):
        return jsonify({"error": "Falta numero (número entero)"}), 400

    try:
        cursor = db().execute("INSERT INTO mesas (numero) VALUES (?)", (numero,))
        db().commit()
    except sqlite3.IntegrityError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"id": cursor.lastrowid, "numero": numero, "estado": "libre"}), 201


@app.patch("/api/mesas/<int:mesa_id>")
def cambiar_estado_mesa(mesa_id):
    datos = request.get_json(silent=True) or {}
    estado = datos.get("estado")

    if estado not in ("libre", "ocupada"):
        return jsonify({"error": "estado debe ser 'libre' u 'ocupada'"}), 400

    cursor = db().execute(
        "UPDATE mesas SET estado = ? WHERE id = ?", (estado, mesa_id)
    )
    db().commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Mesa no encontrada"}), 404

    return jsonify({"id": mesa_id, "estado": estado})


@app.errorhandler(404)
def no_encontrado(e):
    return jsonify({"error": "Ruta no encontrada"}), 404


def ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def iniciar(puerto=3000):
    crear_tablas()
    print(f"Servidor listo en el puerto {puerto}")
    print(f"  En esta computadora:  http://localhost:{puerto}/salud")
    print(f"  Desde las tabletas:   http://{ip_local()}:{puerto}/salud")
    app.run(host="0.0.0.0", port=puerto)
