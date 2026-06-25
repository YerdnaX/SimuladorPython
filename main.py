import sys
import os

# Agregar el directorio raíz del proyecto al path de Python para importaciones relativas.
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from interfaz.tema import obtener_estilo_global
from interfaz.ventana_principal import VentanaPrincipal


# Punto de entrada de la aplicación. Inicializa Qt y lanza la ventana principal.
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Simulador de Planificación de Procesos")
    app.setOrganizationName("CUC")
    app.setStyleSheet(obtener_estilo_global())

    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
