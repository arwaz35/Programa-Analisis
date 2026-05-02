"""
Clase base abstracta para todos los módulos de prueba.
Define la interfaz que cada módulo debe implementar.
"""
import customtkinter as ctk


class BaseModule(ctk.CTkFrame):
    """
    Clase base para módulos de prueba.
    Cada módulo debe implementar:
      - build_ui(): Construir la interfaz del módulo
      - get_data(): Obtener los datos de entrada
      - process(): Ejecutar el análisis
    """

    def __init__(self, parent, data_handler):
        super().__init__(parent)
        self.data_handler = data_handler
        self.build_ui()

    def build_ui(self):
        """Construye la interfaz del módulo. Debe ser implementado por subclases."""
        raise NotImplementedError

    def get_data(self):
        """Retorna los datos de entrada del usuario. Debe ser implementado por subclases."""
        raise NotImplementedError

    def process(self, moto_data, env_conditions, comments):
        """Ejecuta el análisis. Debe ser implementado por subclases."""
        raise NotImplementedError
