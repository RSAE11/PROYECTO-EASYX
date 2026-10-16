# Comanda Jozoca

Aplicación de escritorio para restaurante, hecha en Python.

## Estructura

```
main.py              Punto de entrada: ejecútalo para abrir el programa
app/
  basedatos.py        Crea y conecta la base de datos (SQLite)
  datos_ejemplo.py     Carga categorías y productos de prueba
  interfaz.py          Ventanas y pantallas (Tkinter)
data/                 Se crea sola. Aquí vive tu base de datos real (no se sube a GitHub)
```

## Cómo correrlo

Desde la carpeta raíz del proyecto (donde está `main.py`):

```
python -m app.datos_ejemplo   # solo la primera vez, para tener datos de prueba
python main.py
```

Nota: se usa `python -m app.datos_ejemplo` y no `python app/datos_ejemplo.py`,
porque ese archivo forma parte del paquete `app` y así es como Python lo reconoce.
