"""
app/interfaz.py
Pantalla principal:
  1) Al abrir, muestra las MESAS (libre/ocupada). Tocas una para entrar.
  2) Dentro de una mesa, pantalla de comanda: encabezado, categorías como
     pestañas verticales a la izquierda, productos al centro, el pedido
     a la derecha, y abajo observaciones + totales.
Incluye también "Administrar menú" para agregar categorías y productos.
"""

import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from app.basedatos import obtener_conexion, crear_tablas

COLOR_FONDO = "#1b1d22"
COLOR_BOTON = "#e07a1f"
COLOR_TEXTO_BOTON = "#ffffff"
COLOR_PANEL = "#2a2d34"
COLOR_TEXTO = "#f0f0f0"
COLOR_ACENTO = "#f0a94e"
COLOR_LIBRE = "#2f9e44"
COLOR_OCUPADA = "#c92a2a"
COLOR_PESTAÑA = "#3a3d46"
COLOR_PESTAÑA_ACTIVA = "#e07a1f"

OBSERVACIONES_DISPONIBLES = [
    "Sin cebolla", "Sin picante", "Salsa aparte", "Todo aparte", "Bien cocido",
]


def formatear_precio(precio_centavos):
    return f"${precio_centavos / 100:,.2f}"


class AppComanda(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Comanda Jozoca")
        self.geometry("1150x680")
        self.configure(bg=COLOR_FONDO)

        self.contenedor = tk.Frame(self, bg=COLOR_FONDO)
        self.contenedor.pack(fill="both", expand=True)

        self.mostrar_pantalla_mesas()

    def _limpiar_contenedor(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    # ---------- Pantalla 1: Mesas ----------
    def mostrar_pantalla_mesas(self):
        self._limpiar_contenedor()

        barra_superior = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        barra_superior.pack(side="top", fill="x", padx=16, pady=(16, 8))

        tk.Label(
            barra_superior, text="Mesas", bg=COLOR_FONDO, fg=COLOR_ACENTO,
            font=("Segoe UI", 16, "bold")
        ).pack(side="left")

        tk.Button(
            barra_superior, text="Administrar menú", bg=COLOR_PANEL, fg=COLOR_ACENTO,
            font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=6,
            command=self.abrir_administrar_menu,
        ).pack(side="right")

        tk.Button(
            barra_superior, text="+ Agregar mesa", bg=COLOR_BOTON, fg=COLOR_TEXTO_BOTON,
            font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=6,
            command=self.agregar_mesa,
        ).pack(side="right", padx=(0, 8))

        panel_mesas = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        panel_mesas.pack(fill="both", expand=True, padx=16, pady=8)

        conexion = obtener_conexion()
        mesas = conexion.execute("SELECT * FROM mesas ORDER BY numero").fetchall()
        conexion.close()

        columnas = 5
        for indice, mesa in enumerate(mesas):
            fila, columna = divmod(indice, columnas)
            color = COLOR_LIBRE if mesa["estado"] == "libre" else COLOR_OCUPADA
            texto = f"Mesa {mesa['numero']}\n{mesa['estado'].upper()}"
            boton = tk.Button(
                panel_mesas, text=texto, bg=color, fg="white",
                font=("Segoe UI", 11, "bold"), width=12, height=4, relief="flat",
                command=lambda m=mesa: self.mostrar_pantalla_pedido(m["id"], m["numero"]),
            )
            boton.grid(row=fila, column=columna, padx=8, pady=8)

        if not mesas:
            tk.Label(
                panel_mesas, text="No hay mesas todavía. Usa «+ Agregar mesa».",
                bg=COLOR_FONDO, fg=COLOR_TEXTO, font=("Segoe UI", 11)
            ).pack(pady=20)

    def agregar_mesa(self):
        conexion = obtener_conexion()
        siguiente = conexion.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM mesas").fetchone()[0]
        conexion.execute("INSERT INTO mesas (numero) VALUES (?)", (siguiente,))
        conexion.commit()
        conexion.close()
        self.mostrar_pantalla_mesas()

    # ---------- Pantalla 2: Comanda de una mesa ----------
    def mostrar_pantalla_pedido(self, mesa_id, numero_mesa):
        self._limpiar_contenedor()
        self.pedido_actual = []          # lista de dicts: nombre, precio_centavos, cantidad
        self.observaciones_marcadas = {}  # texto -> BooleanVar
        self.mesa_id_actual = mesa_id
        self.categoria_activa_id = None
        self.botones_categoria = {}

        self._construir_encabezado(numero_mesa)
        self._construir_cuerpo()
        self._construir_pie()

        conexion = obtener_conexion()
        categorias = conexion.execute("SELECT * FROM categorias ORDER BY orden").fetchall()
        conexion.close()

        if not categorias:
            tk.Label(
                self.panel_categorias, text="Agrega categorías\ndesde «Administrar menú»",
                bg=COLOR_FONDO, fg=COLOR_TEXTO, font=("Segoe UI", 9), justify="left"
            ).pack(pady=10, padx=6)
            return

        for categoria in categorias:
            self._agregar_boton_categoria(categoria)

        self._seleccionar_categoria(categorias[0]["id"])

    def _construir_encabezado(self, numero_mesa):
        encabezado = tk.Frame(self.contenedor, bg=COLOR_PANEL)
        encabezado.pack(side="top", fill="x")

        tk.Button(
            encabezado, text="← Mesas", bg=COLOR_PANEL, fg=COLOR_ACENTO,
            font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=10,
            command=self.mostrar_pantalla_mesas,
        ).pack(side="left")

        conexion = obtener_conexion()
        siguiente_comanda = conexion.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM pedidos"
        ).fetchone()[0]
        conexion.close()

        def campo(etiqueta, valor, ancho=12):
            marco = tk.Frame(encabezado, bg=COLOR_PANEL)
            marco.pack(side="left", padx=10, pady=8)
            tk.Label(marco, text=etiqueta, bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 8)).pack(anchor="w")
            entrada = tk.Entry(marco, width=ancho, font=("Segoe UI", 10))
            entrada.insert(0, valor)
            entrada.pack()
            return entrada

        campo("Comanda", str(siguiente_comanda), ancho=6)["state"] = "readonly"
        campo("Fecha", datetime.date.today().strftime("%d/%m/%Y"), ancho=10)
        campo("No. Mesa", str(numero_mesa), ancho=6)
        self.campo_cliente = campo("Cliente", "", ancho=18)

    def _construir_cuerpo(self):
        cuerpo = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        cuerpo.pack(side="top", fill="both", expand=True)

        # Columna izquierda: pestañas verticales de categorías
        self.panel_categorias = tk.Frame(cuerpo, bg=COLOR_PANEL, width=110)
        self.panel_categorias.pack(side="left", fill="y")
        self.panel_categorias.pack_propagate(False)

        # Columna central: productos de la categoría activa
        self.panel_productos = tk.Frame(cuerpo, bg=COLOR_FONDO)
        self.panel_productos.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Columna derecha: el pedido
        panel_pedido = tk.Frame(cuerpo, bg=COLOR_PANEL, width=320)
        panel_pedido.pack(side="right", fill="y")
        panel_pedido.pack_propagate(False)

        cabecera = tk.Frame(panel_pedido, bg=COLOR_PANEL)
        cabecera.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(cabecera, text="Cant", bg=COLOR_PANEL, fg=COLOR_ACENTO, font=("Segoe UI", 9, "bold"), width=4, anchor="w").pack(side="left")
        tk.Label(cabecera, text="Descripción", bg=COLOR_PANEL, fg=COLOR_ACENTO, font=("Segoe UI", 9, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        tk.Label(cabecera, text="Total", bg=COLOR_PANEL, fg=COLOR_ACENTO, font=("Segoe UI", 9, "bold"), width=8, anchor="e").pack(side="right")

        self.lista_pedido = tk.Listbox(
            panel_pedido, bg=COLOR_FONDO, fg=COLOR_TEXTO, bd=0,
            highlightthickness=0, font=("Consolas", 10)
        )
        self.lista_pedido.pack(fill="both", expand=True, padx=10, pady=(0, 6))

    def _construir_pie(self):
        pie = tk.Frame(self.contenedor, bg=COLOR_PANEL)
        pie.pack(side="bottom", fill="x")

        # --- Observaciones (checkboxes) ---
        marco_obs = tk.Frame(pie, bg=COLOR_PANEL)
        marco_obs.pack(side="left", padx=14, pady=10, anchor="n")
        tk.Label(marco_obs, text="Observaciones", bg=COLOR_PANEL, fg=COLOR_ACENTO, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        for texto in OBSERVACIONES_DISPONIBLES:
            variable = tk.BooleanVar(value=False)
            self.observaciones_marcadas[texto] = variable
            tk.Checkbutton(
                marco_obs, text=texto, variable=variable, bg=COLOR_PANEL, fg=COLOR_TEXTO,
                selectcolor=COLOR_FONDO, activebackground=COLOR_PANEL, font=("Segoe UI", 9),
                anchor="w",
            ).pack(anchor="w")

        # --- Opciones del pedido (checkboxes) ---
        marco_opciones = tk.Frame(pie, bg=COLOR_PANEL)
        marco_opciones.pack(side="left", padx=14, pady=10, anchor="n")

        self.variable_servicio = tk.BooleanVar(value=False)
        self.variable_domicilio = tk.BooleanVar(value=False)
        self.variable_para_llevar = tk.BooleanVar(value=False)
        self.variable_pagado = tk.BooleanVar(value=False)
        self.variable_cancelada = tk.BooleanVar(value=False)

        for texto, variable in [
            ("Sumar servicio", self.variable_servicio),
            ("A domicilio", self.variable_domicilio),
            ("Para llevar", self.variable_para_llevar),
            ("Pagado", self.variable_pagado),
            ("Cancelada", self.variable_cancelada),
        ]:
            tk.Checkbutton(
                marco_opciones, text=texto, variable=variable, bg=COLOR_PANEL, fg=COLOR_TEXTO,
                selectcolor=COLOR_FONDO, activebackground=COLOR_PANEL, font=("Segoe UI", 9),
                anchor="w",
            ).pack(anchor="w")

        # --- Mesero / Obser ---
        marco_datos = tk.Frame(pie, bg=COLOR_PANEL)
        marco_datos.pack(side="left", padx=14, pady=10, anchor="n", fill="x", expand=True)

        tk.Label(marco_datos, text="Mesero", bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 9)).pack(anchor="w")
        self.campo_mesero = tk.Entry(marco_datos, font=("Segoe UI", 10))
        self.campo_mesero.pack(fill="x", pady=(0, 6))

        tk.Label(marco_datos, text="Obser.", bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 9)).pack(anchor="w")
        self.campo_observacion_libre = tk.Entry(marco_datos, font=("Segoe UI", 10))
        self.campo_observacion_libre.pack(fill="x")

        # --- Totales + Cerrar comanda ---
        marco_totales = tk.Frame(pie, bg=COLOR_PANEL)
        marco_totales.pack(side="right", padx=14, pady=10, anchor="n")

        tk.Button(
            marco_totales, text="Cerrar comanda", bg=COLOR_LIBRE, fg="white",
            font=("Segoe UI", 11, "bold"), relief="flat", padx=16, pady=10,
            command=self.cerrar_comanda,
        ).pack(pady=(0, 8))

        self.etiqueta_total_productos = tk.Label(marco_totales, text="Total de productos: 0", bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 9))
        self.etiqueta_total_productos.pack(anchor="e")
        self.etiqueta_subtotal = tk.Label(marco_totales, text="Subtotal: $0.00", bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 9))
        self.etiqueta_subtotal.pack(anchor="e")
        self.etiqueta_descuento = tk.Label(marco_totales, text="Descuento: $0.00", bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 9))
        self.etiqueta_descuento.pack(anchor="e")
        self.etiqueta_total = tk.Label(marco_totales, text="Total: $0.00", bg=COLOR_PANEL, fg=COLOR_ACENTO, font=("Segoe UI", 13, "bold"))
        self.etiqueta_total.pack(anchor="e", pady=(4, 0))

    # ---------- Categorías (pestañas verticales) ----------
    def _agregar_boton_categoria(self, categoria):
        boton = tk.Button(
            self.panel_categorias, text=categoria["nombre"], bg=COLOR_PESTAÑA, fg=COLOR_TEXTO,
            font=("Segoe UI", 9, "bold"), relief="flat", wraplength=90, justify="center",
            command=lambda c=categoria["id"]: self._seleccionar_categoria(c),
        )
        boton.pack(fill="x", ipady=14)
        self.botones_categoria[categoria["id"]] = boton

    def _seleccionar_categoria(self, categoria_id):
        self.categoria_activa_id = categoria_id
        for cid, boton in self.botones_categoria.items():
            boton.config(bg=COLOR_PESTAÑA_ACTIVA if cid == categoria_id else COLOR_PESTAÑA)
        self._dibujar_productos(categoria_id)

    def _dibujar_productos(self, categoria_id):
        for widget in self.panel_productos.winfo_children():
            widget.destroy()

        conexion = obtener_conexion()
        productos = conexion.execute(
            "SELECT * FROM productos WHERE categoria_id = ? AND disponible = 1 ORDER BY nombre",
            (categoria_id,),
        ).fetchall()
        conexion.close()

        columnas = 3
        for indice, producto in enumerate(productos):
            fila, columna = divmod(indice, columnas)
            texto = f"{producto['nombre']}\n{formatear_precio(producto['precio_centavos'])}"
            boton = tk.Button(
                self.panel_productos, text=texto, bg=COLOR_BOTON, fg=COLOR_TEXTO_BOTON,
                font=("Segoe UI", 10, "bold"), width=18, height=3, relief="flat",
                command=lambda p=producto: self.agregar_al_pedido(p),
            )
            boton.grid(row=fila, column=columna, padx=6, pady=6)

    # ---------- Pedido ----------
    def agregar_al_pedido(self, producto):
        self.pedido_actual.append({
            "nombre": producto["nombre"],
            "precio_centavos": producto["precio_centavos"],
            "cantidad": 1,
        })
        self._refrescar_lista_pedido()

    def _refrescar_lista_pedido(self):
        self.lista_pedido.delete(0, "end")
        for linea in self.pedido_actual:
            importe = linea["precio_centavos"] * linea["cantidad"]
            texto = f"{linea['cantidad']:>2}  {linea['nombre']:<22}{formatear_precio(importe):>9}"
            self.lista_pedido.insert("end", texto)

        total_productos = sum(linea["cantidad"] for linea in self.pedido_actual)
        subtotal_centavos = sum(linea["precio_centavos"] * linea["cantidad"] for linea in self.pedido_actual)
        descuento_centavos = 0  # por ahora sin lógica de descuento
        total_centavos = subtotal_centavos - descuento_centavos

        self.etiqueta_total_productos.config(text=f"Total de productos: {total_productos}")
        self.etiqueta_subtotal.config(text=f"Subtotal: {formatear_precio(subtotal_centavos)}")
        self.etiqueta_descuento.config(text=f"Descuento: {formatear_precio(descuento_centavos)}")
        self.etiqueta_total.config(text=f"Total: {formatear_precio(total_centavos)}")

    def cerrar_comanda(self):
        if not self.pedido_actual:
            messagebox.showwarning("Comanda vacía", "Agrega al menos un producto antes de cerrar la comanda.")
            return
        # Por ahora solo confirma visualmente; guardar en la base es el siguiente paso.
        messagebox.showinfo(
            "Comanda",
            f"Comanda con {len(self.pedido_actual)} productos lista.\n"
            "(Guardar esto en la base de datos es el siguiente paso que vamos a construir.)"
        )

    # ---------- Administrar menú ----------
    def abrir_administrar_menu(self):
        VentanaAdministrarMenu(self, al_cerrar=self.mostrar_pantalla_mesas)


class VentanaAdministrarMenu(tk.Toplevel):
    """Ventana aparte para agregar categorías y productos, sin tocar código."""

    def __init__(self, padre, al_cerrar):
        super().__init__(padre)
        self.title("Administrar menú")
        self.geometry("420x480")
        self.configure(bg=COLOR_FONDO)
        self.al_cerrar = al_cerrar
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        self._construir_formulario_categoria()
        self._construir_formulario_producto()

    def _construir_formulario_categoria(self):
        tk.Label(
            self, text="Nueva categoría", bg=COLOR_FONDO, fg=COLOR_ACENTO,
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(14, 4), anchor="w", padx=16)

        self.campo_nombre_categoria = tk.Entry(self, font=("Segoe UI", 11))
        self.campo_nombre_categoria.pack(fill="x", padx=16, pady=4)
        self.campo_nombre_categoria.insert(0, "Ej. Entradas")

        tk.Button(
            self, text="Agregar categoría", bg=COLOR_BOTON, fg=COLOR_TEXTO_BOTON,
            font=("Segoe UI", 10, "bold"), relief="flat",
            command=self.guardar_categoria,
        ).pack(padx=16, pady=(4, 14), anchor="w")

    def guardar_categoria(self):
        nombre = self.campo_nombre_categoria.get().strip()
        if not nombre or nombre == "Ej. Entradas":
            messagebox.showwarning("Falta información", "Escribe el nombre de la categoría.")
            return

        conexion = obtener_conexion()
        try:
            orden = conexion.execute("SELECT COALESCE(MAX(orden), -1) + 1 FROM categorias").fetchone()[0]
            conexion.execute(
                "INSERT INTO categorias (nombre, orden) VALUES (?, ?)", (nombre, orden)
            )
            conexion.commit()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
            return
        finally:
            conexion.close()

        self.campo_nombre_categoria.delete(0, "end")
        self._refrescar_lista_categorias()
        messagebox.showinfo("Listo", f"Categoría «{nombre}» agregada.")

    def _construir_formulario_producto(self):
        tk.Label(
            self, text="Nuevo producto", bg=COLOR_FONDO, fg=COLOR_ACENTO,
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(10, 4), anchor="w", padx=16)

        tk.Label(self, text="Categoría", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(anchor="w", padx=16)
        self.combo_categoria = ttk.Combobox(self, state="readonly")
        self.combo_categoria.pack(fill="x", padx=16, pady=(0, 8))
        self._refrescar_lista_categorias()

        tk.Label(self, text="Nombre del producto", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(anchor="w", padx=16)
        self.campo_nombre_producto = tk.Entry(self, font=("Segoe UI", 11))
        self.campo_nombre_producto.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(self, text="Precio (ej. 45.00)", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(anchor="w", padx=16)
        self.campo_precio_producto = tk.Entry(self, font=("Segoe UI", 11))
        self.campo_precio_producto.pack(fill="x", padx=16, pady=(0, 8))

        tk.Button(
            self, text="Agregar producto", bg=COLOR_BOTON, fg=COLOR_TEXTO_BOTON,
            font=("Segoe UI", 10, "bold"), relief="flat",
            command=self.guardar_producto,
        ).pack(padx=16, pady=(4, 14), anchor="w")

    def _refrescar_lista_categorias(self):
        conexion = obtener_conexion()
        categorias = conexion.execute("SELECT id, nombre FROM categorias ORDER BY orden").fetchall()
        conexion.close()

        self.categorias_por_nombre = {c["nombre"]: c["id"] for c in categorias}
        self.combo_categoria["values"] = list(self.categorias_por_nombre.keys())
        if categorias:
            self.combo_categoria.current(0)

    def guardar_producto(self):
        nombre_categoria = self.combo_categoria.get()
        nombre_producto = self.campo_nombre_producto.get().strip()
        texto_precio = self.campo_precio_producto.get().strip()

        if not nombre_categoria:
            messagebox.showwarning("Falta información", "Primero agrega o elige una categoría.")
            return
        if not nombre_producto:
            messagebox.showwarning("Falta información", "Escribe el nombre del producto.")
            return
        try:
            precio = float(texto_precio)
            if precio < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Precio inválido", "Escribe un precio válido, ej. 45.00")
            return

        categoria_id = self.categorias_por_nombre[nombre_categoria]
        precio_centavos = round(precio * 100)

        conexion = obtener_conexion()
        try:
            conexion.execute(
                "INSERT INTO productos (categoria_id, nombre, precio_centavos) VALUES (?, ?, ?)",
                (categoria_id, nombre_producto, precio_centavos),
            )
            conexion.commit()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
            return
        finally:
            conexion.close()

        self.campo_nombre_producto.delete(0, "end")
        self.campo_precio_producto.delete(0, "end")
        messagebox.showinfo("Listo", f"«{nombre_producto}» agregado a {nombre_categoria}.")

    def _cerrar(self):
        self.al_cerrar()
        self.destroy()
