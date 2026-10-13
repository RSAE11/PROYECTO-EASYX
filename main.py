"""
main.py
Punto de entrada del programa. Esto es lo único que ejecutas
para prender la aplicación.
"""

from app.basedatos import crear_tablas
from app.interfaz import AppComanda

if __name__ == "__main__":
    crear_tablas()
    app = AppComanda()
    app.mainloop()
