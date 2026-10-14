"""
app/interfaz.py
Primera pantalla del sistema: muestra el menú por categorías,
con botones para cada producto.
"""

import tkinter as tk
from tkinter import ttk

from app.basedatos import obtener_conexion, crear_tablas

COLOR_FONDO = "#1b1d22"
COLOR_BOTON = "#e07a1f"
COLOR_TEXTO_BOTON = "#ffffff"
COLOR_PANEL = "#2a2d34"
COLOR_TEXTO = "#f0f0f0"
COLOR_ACENTO = "#f0a94e"


def formatear_precio(precio_centavos):
    return f"${precio_centavos / 100:,.2f}"


class AppComanda(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Comanda Jozoca")
        self.geometry("900x600")
        self.configure(bg=COLOR_FONDO)

        self.pedido_actual = []

        self._construir_layout()
        self._cargar_categorias()

    def _construir_layout(self):
        panel_izquierdo = tk.Frame(self, bg=COLOR_FONDO)
        panel_izquierdo.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.pestañas = ttk.Notebook(panel_izquierdo)
        self.pestañas.pack(fill="both", expand=True)

        panel_derecho = tk.Frame(self, bg=COLOR_PANEL, width=280)
        panel_derecho.pack(side="right", fill="y")
        panel_derecho.pack_propagate(False)

        tk.Label(
            panel_derecho, text="Pedido actual", bg=COLOR_PANEL, fg=COLOR_ACENTO,
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(14, 8))

        self.lista_pedido = tk.Listbox(
            panel_derecho, bg=COLOR_FONDO, fg=COLOR_TEXTO, bd=0,
            highlightthickness=0, font=("Segoe UI", 11)
        )
        self.lista_pedido.pack(fill="both", expand=True, padx=10)

        self.etiqueta_total = tk.Label(
            panel_derecho, text="Total: $0.00", bg=COLOR_PANEL, fg=COLOR_TEXTO,
            font=("Segoe UI", 13, "bold")
        )
        self.etiqueta_total.pack(pady=10)

    def _cargar_categorias(self):
        conexion = obtener_conexion()
        categorias = conexion.execute("SELECT * FROM categorias ORDER BY orden").fetchall()

        for categoria in categorias:
            pestaña = tk.Frame(self.pestañas, bg=COLOR_FONDO)
            self.pestañas.add(pestaña, text=categoria["nombre"])
            self._llenar_pestaña(pestaña, categoria["id"], conexion)

        conexion.close()

    def _llenar_pestaña(self, pestaña, categoria_id, conexion):
        productos = conexion.execute(
            "SELECT * FROM productos WHERE categoria_id = ? AND disponible = 1 ORDER BY nombre",
            (categoria_id,),
        ).fetchall()

        columnas = 3
        for indice, producto in enumerate(productos):
            fila, columna = divmod(indice, columnas)
            texto = f"{producto['nombre']}\n{formatear_precio(producto['precio_centavos'])}"
            boton = tk.Button(
                pestaña, text=texto, bg=COLOR_BOTON, fg=COLOR_TEXTO_BOTON,
                font=("Segoe UI", 10, "bold"), width=18, height=3, relief="flat",
                command=lambda p=producto: self.agregar_al_pedido(p),
            )
            boton.grid(row=fila, column=columna, padx=6, pady=6)

    def agregar_al_pedido(self, producto):
        self.pedido_actual.append((producto["nombre"], producto["precio_centavos"]))
        self.lista_pedido.insert(
            "end", f"{producto['nombre']}  {formatear_precio(producto['precio_centavos'])}"
        )
        total = sum(precio for _, precio in self.pedido_actual)
        self.etiqueta_total.config(text=f"Total: {formatear_precio(total)}")
