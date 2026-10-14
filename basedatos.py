"""
app/basedatos.py
Crea la base de datos del sistema de comandas (si no existe todavía)
y deja lista una conexión para usarla desde otros archivos.
"""

import sqlite3
import os

# La carpeta "data" vive en la raíz del proyecto, un nivel arriba de "app"
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_DATOS = os.path.join(RAIZ_PROYECTO, "data")
RUTA_BASE_DATOS = os.path.join(CARPETA_DATOS, "comanda.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS categorias (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL UNIQUE,
    orden   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS productos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id     INTEGER NOT NULL REFERENCES categorias(id),
    nombre           TEXT NOT NULL,
    precio_centavos  INTEGER NOT NULL CHECK (precio_centavos >= 0),
    disponible       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mesas (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    numero  INTEGER NOT NULL UNIQUE,
    estado  TEXT NOT NULL DEFAULT 'libre' CHECK (estado IN ('libre', 'ocupada'))
);

CREATE TABLE IF NOT EXISTS pedidos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mesa_id         INTEGER NOT NULL REFERENCES mesas(id),
    mesero          TEXT,
    estado          TEXT NOT NULL DEFAULT 'abierto'
                    CHECK (estado IN ('abierto', 'en_cocina', 'listo', 'entregado', 'pagado', 'cancelado')),
    creado_en       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detalle_pedido (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id                 INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_id               INTEGER NOT NULL REFERENCES productos(id),
    cantidad                  INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario_centavos  INTEGER NOT NULL CHECK (precio_unitario_centavos >= 0),
    notas                     TEXT
);

CREATE TABLE IF NOT EXISTS pagos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id      INTEGER NOT NULL REFERENCES pedidos(id),
    metodo         TEXT NOT NULL CHECK (metodo IN ('efectivo', 'tarjeta', 'transferencia')),
    monto_centavos INTEGER NOT NULL CHECK (monto_centavos > 0),
    creado_en      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def obtener_conexion():
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas():
    conexion = obtener_conexion()
    conexion.executescript(ESQUEMA)
    conexion.commit()
    conexion.close()
    print(f"Base de datos lista en: {RUTA_BASE_DATOS}")


if __name__ == "__main__":
    crear_tablas()
