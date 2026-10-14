"""
app/datos_ejemplo.py
Mete categorías y productos de ejemplo a la base de datos.
Los precios están en CENTAVOS: $45.00 se escribe como 4500.
"""

from app.basedatos import obtener_conexion, crear_tablas

CATEGORIAS_Y_PRODUCTOS = {
    "Entradas": [
        ("Ensalada César", 8500),
        ("Sopa del día", 6500),
        ("Queso fundido", 9500),
        ("Alitas BBQ", 11000),
    ],
    "Platos fuertes": [
        ("Milanesa de pollo", 12500),
        ("Arrachera", 18500),
        ("Filete de pescado", 16500),
        ("Enchiladas verdes", 11000),
        ("Pasta alfredo", 10500),
    ],
    "Bebidas": [
        ("Refresco", 3500),
        ("Agua fresca", 3000),
        ("Café", 3000),
        ("Cerveza", 5500),
        ("Limonada", 3500),
    ],
    "Postres": [
        ("Pastel de chocolate", 6500),
        ("Flan", 5500),
        ("Helado", 5000),
    ],
}


def cargar_datos_ejemplo():
    crear_tablas()
    conexion = obtener_conexion()

    for orden, (nombre_categoria, productos) in enumerate(CATEGORIAS_Y_PRODUCTOS.items()):
        conexion.execute(
            "INSERT OR IGNORE INTO categorias (nombre, orden) VALUES (?, ?)",
            (nombre_categoria, orden),
        )
        fila = conexion.execute(
            "SELECT id FROM categorias WHERE nombre = ?", (nombre_categoria,)
        ).fetchone()
        categoria_id = fila["id"]

        for nombre_producto, precio_centavos in productos:
            conexion.execute(
                "INSERT OR IGNORE INTO productos (categoria_id, nombre, precio_centavos) VALUES (?, ?, ?)",
                (categoria_id, nombre_producto, precio_centavos),
            )

    conexion.commit()
    conexion.close()
    print("Categorías y productos de ejemplo cargados.")


if __name__ == "__main__":
    cargar_datos_ejemplo()
