"""
Módulo de Frenado - Esqueleto para implementación futura.
"""
import customtkinter as ctk
from modules.base_module import BaseModule


class BrakingModule(BaseModule):
    def build_ui(self):
        ctk.CTkLabel(self, text="Prueba de Frenado", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(self, text="⚠ Este módulo aún no está implementado.",
                     font=("Arial", 14), text_color="orange").pack(pady=20)

    def get_data(self):
        return []

    def process(self, moto_data, env_conditions, comments):
        return False, "Módulo de frenado no implementado aún."
