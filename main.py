"""
Programa Análisis de Datos - INCOL
Punto de entrada principal.

Versión 1.1.0
"""
import sys
import os
import customtkinter as ctk
from tkinter import messagebox
import threading

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from version import VERSION
from config import ensure_directories
from data_handler import DataHandler
from modules.acceleration import AccelerationModule
from modules.braking import BrakingModule
from modules.climbing import ClimbingModule
from modules.top_speed import TopSpeedModule
from ui.management.motos_view import show_gestion_motos
from ui.management.pilotos_view import show_gestion_pilotos
from ui.management.lugares_view import show_gestion_lugares


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"INCOL - Análisis de Datos v{VERSION}")
        self.geometry("1200x750")
        ctk.set_appearance_mode("light")

        # Forzar que la ventana aparezca en primer plano (especial para macOS)
        self.lift()
        self.attributes('-topmost', True)
        self.after(200, lambda: self.attributes('-topmost', False))
        if sys.platform == 'darwin':
            os.system(f'''/usr/bin/osascript -e 'tell app "System Events" to set frontmost of first process whose unix id is {os.getpid()} to true' ''')

        # Inicializar
        ensure_directories()
        self.data_handler = DataHandler()

        # Módulo activo y modo
        self.current_module = None
        self.current_mode = "individual"

        # Mostrar menú principal
        self.show_main_menu()

    def clear_window(self):
        """Elimina todos los widgets de la ventana."""
        for widget in self.winfo_children():
            widget.destroy()
        self.current_module = None

    # ══════════════════════════════════════════════════
    # MENÚ PRINCIPAL
    # ══════════════════════════════════════════════════
    def show_main_menu(self):
        self.clear_window()

        # Contenedor central
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.4, anchor="center")

        ctk.CTkLabel(center, text="INCOL", font=("Arial", 40, "bold")).pack(pady=(0, 5))
        ctk.CTkLabel(center, text="Sistema de Análisis de Datos",
                     font=("Arial", 18)).pack(pady=(0, 5))
        ctk.CTkLabel(center, text=f"Versión {VERSION}",
                     font=("Arial", 12), text_color="gray").pack(pady=(0, 20))

        # Botones principales de análisis
        analysis_frame = ctk.CTkFrame(center, fg_color="transparent")
        analysis_frame.pack(pady=10)

        ctk.CTkButton(analysis_frame, text="🔬 Individual",
                      font=("Arial", 16, "bold"), height=48, width=280,
                      fg_color="#2196F3", hover_color="#1976D2",
                      command=lambda: self.show_test_selection(mode="individual")).pack(pady=5)

        ctk.CTkButton(analysis_frame, text="⚖️ Comparación",
                      font=("Arial", 16, "bold"), height=48, width=280,
                      fg_color="#3F51B5", hover_color="#303F9F",
                      command=lambda: self.show_test_selection(mode="comparison")).pack(pady=5)

        # Botones de gestión
        mgmt = ctk.CTkFrame(center, fg_color="transparent")
        mgmt.pack(pady=15)

        btns = [
            ("🏍 Gestión de Motos", "#4CAF50", "#388E3C", lambda: show_gestion_motos(self)),
            ("👤 Gestión de Pilotos", "#4CAF50", "#388E3C", lambda: show_gestion_pilotos(self)),
            ("📍 Gestión de Lugares", "#4CAF50", "#388E3C", lambda: show_gestion_lugares(self)),
        ]
        for txt, fg, hv, cmd in btns:
            ctk.CTkButton(mgmt, text=txt, font=("Arial", 14, "bold"),
                         height=40, width=250, fg_color=fg, hover_color=hv,
                         text_color="white", command=cmd).pack(pady=4)

    # ══════════════════════════════════════════════════
    # SELECCIÓN DE PRUEBAS (INDIVIDUAL / COMPARACIÓN)
    # ══════════════════════════════════════════════════
    def show_test_selection(self, mode="individual"):
        self.clear_window()
        self.current_mode = mode

        title_text = "Pruebas Individuales" if mode == "individual" else "Comparación de Pruebas"

        # --- Barra superior ---
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(top_bar, text="⬅ Menú Principal", font=("Arial", 12),
                      fg_color="gray", hover_color="darkgray",
                      command=self.show_main_menu).pack(side="left", padx=10)
        ctk.CTkLabel(top_bar, text=title_text,
                     font=("Arial", 20, "bold")).pack(side="left", padx=20)

        # --- Contenido principal (2 columnas) ---
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Columna izquierda: controles
        left = ctk.CTkFrame(main_frame, width=320)
        left.pack(side="left", fill="y", padx=10, pady=5)
        left.pack_propagate(False)

        # Selector de prueba
        ctk.CTkLabel(left, text="🔬 Tipo de prueba", font=("Arial", 14, "bold")).pack(pady=(10, 5), padx=10, anchor="w")

        test_types = [
            ("Aceleración y Recuperación", "#2196F3", "#1976D2", "accel"),
            ("Frenado", "#2196F3", "#1976D2", "brake"),
            ("Ascenso", "#2196F3", "#1976D2", "climb"),
            ("Velocidad Máxima", "#2196F3", "#1976D2", "topspeed"),
        ]
        for txt, fg, hv, key in test_types:
            ctk.CTkButton(left, text=txt, font=("Arial", 13, "bold"),
                         height=40, width=270, fg_color=fg, hover_color=hv,
                         command=lambda k=key: self._load_module(k, mode)).pack(pady=3, padx=10)

        # Condiciones ambientales
        ctk.CTkLabel(left, text="🌡 Condiciones ambientales",
                     font=("Arial", 14, "bold")).pack(pady=(20, 5), padx=10, anchor="w")

        env_frame = ctk.CTkFrame(left)
        env_frame.pack(fill="x", padx=10, pady=5)

        env_fields = [("Temp. Ambiente (°C):", "temp_amb"),
                      ("Humedad (%):", "humidity"),
                      ("Temp. Suelo (°C):", "temp_ground")]

        self.env_entries = {}
        for label, key in env_fields:
            r = ctk.CTkFrame(env_frame, fg_color="transparent")
            r.pack(fill="x", padx=5, pady=3)
            ctk.CTkLabel(r, text=label, font=("Arial", 11)).pack(side="left")
            e = ctk.CTkEntry(r, width=80)
            e.pack(side="right")
            self.env_entries[key] = e

        # Comentarios
        ctk.CTkLabel(left, text="📝 Comentarios", font=("Arial", 14, "bold")).pack(pady=(15, 5), padx=10, anchor="w")
        self.comments_entry = ctk.CTkTextbox(left, height=80, width=270)
        self.comments_entry.pack(padx=10, pady=(0, 10))

        # Botón Previsualizar
        self.btn_preview = ctk.CTkButton(left, text="👁 Previsualizar",
                                         font=("Arial", 16, "bold"), height=50, width=270,
                                         fg_color="#107C41", hover_color="#0b5e31",
                                         command=self._run_preview)
        self.btn_preview.pack(pady=15, padx=10)

        # Columna derecha: módulo dinámico
        self.module_frame = ctk.CTkFrame(main_frame)
        self.module_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(self.module_frame, text="Seleccione un tipo de prueba",
                     font=("Arial", 16), text_color="gray").pack(expand=True)

    def _load_module(self, module_key, mode="individual"):
        """Carga el módulo de prueba correspondiente."""
        for w in self.module_frame.winfo_children():
            w.destroy()

        if mode == "comparison" and module_key == "climb":
            placeholder = ctk.CTkFrame(self.module_frame, fg_color="transparent")
            placeholder.pack(expand=True)
            ctk.CTkLabel(placeholder, text="🚧 Módulo en Construcción",
                         font=("Arial", 20, "bold")).pack(pady=10)
            ctk.CTkLabel(placeholder,
                         text="La comparación de pruebas de ascenso estará disponible\nen una próxima actualización.\n\nPuede utilizar la sección 'Individual' para analizar pruebas de ascenso.",
                         font=("Arial", 13), text_color="gray", justify="center").pack(pady=10)
            self.current_module = None
            return

        modules = {
            "accel": AccelerationModule,
            "brake": BrakingModule,
            "climb": ClimbingModule,
            "topspeed": TopSpeedModule,
        }

        cls = modules.get(module_key)
        if cls:
            self.current_module = cls(self.module_frame, self.data_handler, mode=mode)
            self.current_module.pack(fill="both", expand=True)

    def _get_env_conditions(self):
        """Obtiene las condiciones ambientales del formulario."""
        cond = {}
        for key, entry in self.env_entries.items():
            val = entry.get().strip()
            cond[key] = val if val else ''

        # Buscar datos del lugar seleccionado desde el módulo activo
        if self.current_module:
            inputs = self.current_module.get_data()
            if inputs and len(inputs) > 0:
                cond['lugar'] = inputs[0].get('lugar_data', {})
            else:
                cond['lugar'] = {}
        else:
            cond['lugar'] = {}

        return cond

    def _get_moto_data(self):
        """Obtiene los datos de la moto seleccionada en el módulo activo."""
        if self.current_module:
            inputs = self.current_module.get_data()
            if inputs and len(inputs) > 0:
                return inputs[0].get('moto_data', {})
        return {}

    def _run_preview(self):
        """Ejecuta el análisis y abre la previsualización."""
        if not self.current_module:
            messagebox.showwarning("Aviso", "Seleccione un tipo de prueba primero.")
            return

        moto_data = self._get_moto_data()
        env_conditions = self._get_env_conditions()
        comments = self.comments_entry.get("1.0", "end").strip()

        self.btn_preview.configure(state="disabled", text="⏳ Procesando...")

        def run():
            try:
                ok, msg = self.current_module.process(moto_data, env_conditions, comments)
                if not ok:
                    self.after(0, lambda: messagebox.showerror("Error", msg))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.after(0, lambda: self.btn_preview.configure(state="normal", text="👁 Previsualizar"))

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
