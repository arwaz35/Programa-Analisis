"""
Módulo de Ascenso.
Evalúa la capacidad de la motocicleta para ascender en pendiente (~12°).
Dos condiciones: solo piloto (Archivo 1) y piloto + pasajero (Archivo 2).
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pandas as pd

from modules.base_module import BaseModule
from utils.csv_parser import parse_csv, convert_units
from utils.event_detector import (extract_climbing_events, refine_acceleration_start,
                                   export_event_to_csv)
from utils.metrics_calculator import calculate_climbing_metrics, calculate_slope
from utils.gps_utils import get_gps_context
from plotting.speed_plotter import plot_speed_comparison, plot_speed_detailed
from plotting.accel_plotter import plot_accel_vs_time
from plotting.rpm_plotter import plot_rpm_vs_time
from plotting.map_plotter import plot_gps_heatmap, plot_gps_route_simple
from config import RESULTADOS_DIR, MAX_SPEED_DROP_KMH

# ══════════════════════════════════════════════════════════════════════
# MAPEO DE CELDAS EXCEL - Formato ft-nm-000-012.xlsx
# Modificar aquí para ajustar las posiciones de datos e imágenes.
# ══════════════════════════════════════════════════════════════════════
EXCEL_CELLS = {
    # --- General Information ---
    "modelo_codigo": "B9",
    "fecha": "N7",
    "origen": "N8",
    "placa": "N9",
    "chasis": "N10",
    "motor": "N11",
    "foto_moto": "Y7",

    # --- Conclusion ---
    "comentarios": "A38",

    # --- Conditions ---
    "piloto_nombre": "B44",
    "piloto_peso": "B45",
    "piloto_altura": "B46",
    "piloto_foto": "B48",
    "pasajero_nombre": "J44",
    "pasajero_peso": "J45",
    "pasajero_altura": "J46",
    "pasajero_foto": "J48",
    "lugar_nombre": "W44",
    "lugar_altitud": "W45",
    "lugar_coordenadas": "W46",
    "lugar_link": "W47",
    "temp_ambiente": "AG44",
    "humedad": "AG45",
    "temp_suelo": "AG46",
    "mapa_trazado": "T49",

    # --- Ascenso Solo Piloto: Tabla mejores eventos ---
    "climb_pilot_start_row": 73,
    "climb_pilot_col_num": "B",
    "climb_pilot_col_evento": "C",
    "climb_pilot_col_vi": "E",
    "climb_pilot_col_vf": "G",
    "climb_pilot_col_tiempo": "I",
    "climb_pilot_col_dist": "K",
    "climb_pilot_col_acel": "M",
    "climb_pilot_col_rpm": "O",
    "climb_pilot_img_resumen": "R69",

    # --- Ascenso Piloto + Pasajero: Tabla mejores eventos ---
    "climb_pax_start_row": 93,
    "climb_pax_col_num": "B",
    "climb_pax_col_evento": "C",
    "climb_pax_col_vi": "E",
    "climb_pax_col_vf": "G",
    "climb_pax_col_tiempo": "I",
    "climb_pax_col_dist": "K",
    "climb_pax_col_acel": "M",
    "climb_pax_col_rpm": "O",
    "climb_pax_img_resumen": "R89",

    # --- Best Event Ascenso Solo Piloto ---
    "best_climb_pilot_row": 115,
    "best_climb_pilot_img_vel": "R111",
    "best_climb_pilot_img_acel": "R123",
    "best_climb_pilot_img_rpm": "R129",
    "best_climb_pilot_img_mapa": "B117",

    # --- Best Event Ascenso Piloto + Pasajero ---
    "best_climb_pax_row": 140,
    "best_climb_pax_img_vel": "R136",
    "best_climb_pax_img_acel": "R148",
    "best_climb_pax_img_rpm": "R154",
    "best_climb_pax_img_mapa": "B142",
}

# Tamaños de imágenes para Excel (Alto cm, Ancho cm)
EXCEL_IMG_SIZES = {
    "mapa": (10.5, 15.5),
    "grafica_resumen": (11.5, 17.5),
    "grafica_vel": (7.0, 17.5),
    "grafica_small": (4.0, 17.5),
}

# Etiquetas de condiciones de carga
CLIMB_LABELS = {
    1: "Rider Only",
    2: "Rider + Passenger"
}


class ClimbingModule(BaseModule):
    def build_ui(self):
        ctk.CTkLabel(self, text="Prueba de Ascenso",
                     font=("Arial", 16, "bold")).pack(pady=10)

        self.files_frame = ctk.CTkFrame(self)
        self.files_frame.pack(fill="x", padx=10, pady=5)

        # Lugar general (compartido para ambos archivos)
        lugar_row = ctk.CTkFrame(self.files_frame)
        lugar_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(lugar_row, text="Lugar:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.lugar_combo = ctk.CTkComboBox(lugar_row, values=["Seleccione Lugar..."], width=200)
        self.lugar_combo.pack(side="left", padx=5)

        # Fila 1: Solo piloto
        self._create_file_row(self.files_frame, 1, "Archivo 1 (Solo Piloto):", has_passenger=False)
        # Fila 2: Piloto + pasajero
        self._create_file_row(self.files_frame, 2, "Archivo 2 (Con Pasajero):", has_passenger=True)

        self.refresh_combos()

    def _create_file_row(self, parent, num, label, has_passenger=False):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(row, text=label, font=("Arial", 12, "bold")).pack(side="left", padx=5)

        # Moto combo
        moto_combo = ctk.CTkComboBox(row, values=["Seleccione Moto..."], width=150)
        moto_combo.pack(side="left", padx=5)

        # Piloto combo
        pilot_combo = ctk.CTkComboBox(row, values=["Seleccione Piloto..."], width=130)
        pilot_combo.pack(side="left", padx=5)

        # Pasajero combo (solo para fila 2)
        if has_passenger:
            pax_combo = ctk.CTkComboBox(row, values=["Seleccione Pasajero..."], width=130)
            pax_combo.pack(side="left", padx=5)
            setattr(self, f'pax_combo_{num}', pax_combo)

        # Ruta del archivo
        path_entry = ctk.CTkEntry(row, width=150, placeholder_text="Ruta del archivo CSV...")
        path_entry.pack(side="left", padx=5, fill="x", expand=True)

        def browse():
            f = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")])
            if f:
                path_entry.delete(0, "end")
                path_entry.insert(0, f)

        ctk.CTkButton(row, text="Buscar", width=60, command=browse).pack(side="left", padx=5)

        setattr(self, f'moto_combo_{num}', moto_combo)
        setattr(self, f'pilot_combo_{num}', pilot_combo)
        setattr(self, f'path_entry_{num}', path_entry)

    def refresh_combos(self):
        """Actualiza las listas de motos, pilotos y lugares."""
        motos = self.data_handler.load_motos()
        moto_names = [f"{m.get('Nombre Comercial', '')} - {m.get('Placa', '')}" for m in motos]
        if not moto_names:
            moto_names = ["Sin motos registradas"]

        pilotos = self.data_handler.load_pilotos()
        pilot_names = [p.get('nombre', '') for p in pilotos]
        if not pilot_names:
            pilot_names = ["Sin pilotos"]

        lugares = self.data_handler.load_lugares()
        lugar_names = [l.get('Nombre', '') for l in lugares]
        if not lugar_names:
            lugar_names = ["Sin lugares registrados"]

        self.lugar_combo.configure(values=lugar_names)

        for num in [1, 2]:
            getattr(self, f'moto_combo_{num}').configure(values=moto_names)
            getattr(self, f'pilot_combo_{num}').configure(values=pilot_names)

        # Pasajero en fila 2
        if hasattr(self, 'pax_combo_2'):
            self.pax_combo_2.configure(values=pilot_names)

    def get_data(self):
        """Retorna lista de inputs válidos (hasta 2 archivos)."""
        inputs = []
        pilotos_data = self.data_handler.load_pilotos()
        motos_data = self.data_handler.load_motos()
        lugares_data = self.data_handler.load_lugares()

        lugar_str = self.lugar_combo.get()
        lugar_data = {}
        for l in lugares_data:
            if l.get('Nombre', '') == lugar_str:
                lugar_data = l
                break
        else:
            lugar_data = {'Nombre': lugar_str}

        for num in [1, 2]:
            path = getattr(self, f'path_entry_{num}').get()
            pilot = getattr(self, f'pilot_combo_{num}').get()
            moto_str = getattr(self, f'moto_combo_{num}').get()

            if not path or not os.path.exists(path):
                continue
            if pilot in ["Seleccione Piloto...", "Sin pilotos"]:
                continue

            weight = 0
            altura = 0
            for p in pilotos_data:
                if p.get('nombre') == pilot:
                    weight = p.get('peso', 0)
                    altura = p.get('altura', 0)
                    break

            moto_data = {}
            for m in motos_data:
                check = f"{m.get('Nombre Comercial', '')} - {m.get('Placa', '')}"
                if check == moto_str:
                    moto_data = m
                    break

            # Pasajero (solo fila 2)
            passenger = None
            pax_weight = 0
            pax_altura = 0
            if num == 2 and hasattr(self, 'pax_combo_2'):
                pax_name = self.pax_combo_2.get()
                if pax_name not in ["Seleccione Pasajero...", "Sin pilotos"]:
                    passenger = pax_name
                    for p in pilotos_data:
                        if p.get('nombre') == pax_name:
                            pax_weight = p.get('peso', 0)
                            pax_altura = p.get('altura', 0)
                            break

            inputs.append({
                'filepath': path,
                'pilot': pilot,
                'weight': str(weight),
                'altura': str(altura),
                'moto_data': moto_data,
                'lugar_data': lugar_data,
                'passenger': passenger,
                'pax_weight': str(pax_weight),
                'pax_altura': str(pax_altura),
                'condition': CLIMB_LABELS.get(num, f"Condition {num}"),
                'file_num': num
            })

        return inputs

    def process(self, moto_data, env_conditions, comments):
        """Ejecuta el análisis de ascenso."""
        valid_inputs = self.get_data()

        if not valid_inputs:
            messagebox.showerror("Error", "Debe seleccionar al menos un archivo válido con piloto.")
            return False, "Sin entradas válidas"

        try:
            return self._process_climbing(valid_inputs, moto_data, env_conditions, comments)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error en análisis: {str(e)}"

    def _process_climbing(self, inputs, moto_data, env_conditions, comments):
        """Procesa 1 o 2 archivos de ascenso (cada uno independiente)."""
        climbing_results = {}
        slope_data = None

        for inp in inputs:
            df = parse_csv(inp['filepath'])
            if df.empty:
                continue
            df = convert_units(df)

            file_num = inp['file_num']
            condition = inp['condition']

            raw_events = extract_climbing_events(df, target_distance=70)
            valid_events = []
            seen_starts = set()
            for evt_df in raw_events:
                s_idx = evt_df.attrs.get('start_idx', evt_df.index[0])
                e_idx = evt_df.attrs.get('end_idx', evt_df.index[-1])

                # Refinar inicio
                s_idx_refined = refine_acceleration_start(evt_df)

                # Evitar duplicados del mismo despegue físico
                if s_idx_refined in seen_starts:
                    continue
                seen_starts.add(s_idx_refined)

                # Recortar el DataFrame del evento para que el buffer previo sea de exactamente 20 muestras (2.0s)
                # respecto al despegue real (s_idx_refined), eliminando tiempos muertos prolongados en reposo.
                ref_loc = evt_df.index.get_loc(s_idx_refined)
                new_slice_start = max(0, ref_loc - 20)
                trimmed_df = evt_df.iloc[new_slice_start:].copy()
                trimmed_df.attrs = evt_df.attrs.copy()
                trimmed_df.attrs['start_idx'] = s_idx_refined

                # Validar continuidad de aceleración (descartar intentos con caídas >= MAX_SPEED_DROP_KMH)
                phase_v = trimmed_df.loc[s_idx_refined:e_idx, 'Velocidad_GPS']
                peak_v = 0.0
                has_excessive_drop = False
                for v in phase_v:
                    if v > peak_v:
                        peak_v = v
                    if peak_v >= 8.0 and (peak_v - v) >= MAX_SPEED_DROP_KMH:
                        has_excessive_drop = True
                        break
                if has_excessive_drop:
                    continue

                m = calculate_climbing_metrics(trimmed_df, s_idx_refined, e_idx)
                if m:
                    valid_events.append({
                        'df': trimmed_df, 'metrics': m, 'pilot': inp['pilot'],
                        'weight': inp['weight'], 'id': len(valid_events) + 1,
                        'condition': condition
                    })

                    # Calcular pendiente (del primer evento válido)
                    if slope_data is None:
                        slope_data = calculate_slope(trimmed_df, s_idx_refined, e_idx)

            if valid_events:
                valid_events.sort(key=lambda x: x['metrics']['time_s'])
                climbing_results[file_num] = {
                    'best': valid_events[0],
                    'top_3': valid_events[:3],
                    'condition': condition,
                    'input': inp,
                    'df': df
                }

        if not climbing_results:
            return False, "No se encontraron eventos válidos de ascenso."

        # --- CONSTRUIR DATOS DE PREVIEW ---
        first_df = list(climbing_results.values())[0]['df']
        contexto_gps = get_gps_context(first_df)

        max_dist = 0.0
        for fn, res in climbing_results.items():
            for ev in res['top_3']:
                m = ev.get('metrics')
                if m and m.get('dist_m', 0) > max_dist:
                    max_dist = m['dist_m']
        if max_dist <= 0:
            max_dist = contexto_gps.get('distancia_m', 0.0)

        context_map = None
        first_best = list(climbing_results.values())[0]['best']
        context_map_buf = plot_gps_route_simple(first_best['df'], distance_m=max_dist,
                                                 slope_data=slope_data)
        if context_map_buf:
            context_map = context_map_buf.getvalue()

        sections = []
        preview_data = {
            "type": "climbing",
            "moto_info": moto_data,
            "inputs": inputs,
            "comments": comments,
            "env_conditions": env_conditions,
            "sections": sections,
            "contexto_gps": contexto_gps,
            "context_map": context_map,
            "climbing_data": {},
            "slope_data": slope_data,
            "excel_cells": EXCEL_CELLS,
            "excel_img_sizes": EXCEL_IMG_SIZES,
        }

        for file_num in [1, 2]:
            if file_num not in climbing_results:
                continue

            res = climbing_results[file_num]
            top_3 = res['top_3']
            best = res['best']
            condition = res['condition']

            for i, ev in enumerate(top_3):
                ev['display_name'] = f"Event {ev['id']}"

            img_combined = plot_speed_comparison(top_3, f"Climbing {condition} - General Result")

            sections.append({
                "title": f"Climbing {condition} - Summary",
                "images": [{'bytes': img_combined.getvalue()}],
                "table_data": None
            })

            img_detail_v = plot_speed_detailed(best, "Speed vs Time")
            img_detail_a = plot_accel_vs_time(best, "Acceleration vs Time")
            img_detail_rpm = plot_rpm_vs_time(best, "RPM vs Time") if 'RPM' in best['df'].columns else None
            img_detail_gps = plot_gps_heatmap(best, "Ubicación de la prueba")

            m = best['metrics']
            tab_b = [["V. Start (km/h)", "V. End (km/h)", "Time (s)", "Distance (m)", "Avg Acc (m/s²)", "Top RPM"],
                     [f"{m['v_start']:.2f}", f"{m['v_final']:.2f}", f"{m['time_s']:.2f}",
                      f"{m['dist_m']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"]]

            imgs_detalle = []
            if img_detail_gps:
                imgs_detalle.append({'bytes': img_detail_gps.getvalue()})
            imgs_detalle.append({'bytes': img_detail_v.getvalue()})
            if img_detail_rpm:
                imgs_detalle.append({'bytes': img_detail_rpm.getvalue()})
            imgs_detalle.append({'bytes': img_detail_a.getvalue()})

            sections.append({
                "title": f"Climbing {condition} - Best Event ({res['input']['pilot']})",
                "images": imgs_detalle,
                "table_data": tab_b
            })

            preview_data["climbing_data"][file_num] = {
                "top_3_events": top_3,
                "best_event": best,
                "condition": condition,
                "img_combined": img_combined.getvalue(),
                "img_detail_v": img_detail_v.getvalue(),
                "img_detail_a": img_detail_a.getvalue(),
                "img_detail_rpm": img_detail_rpm.getvalue() if img_detail_rpm else None,
                "img_detail_gps": img_detail_gps.getvalue() if img_detail_gps else None,
            }

        from ui.preview_window import PreviewWindow

        def on_excel(p_data):
            from reports.excel_reporter import ExcelReporter
            try:
                r = ExcelReporter()
                ok, path = r.generate_climbing(p_data)
                if ok:
                    messagebox.showinfo("Excel Guardado", f"Generado en:\n{path}")
                else:
                    messagebox.showerror("Excel Error", f"Error:\n{path}")
            except Exception as e:
                messagebox.showerror("Excel Exception", str(e))

        PreviewWindow(self, "Previsualización - Ascenso",
                      sections, on_excel_callback=on_excel,
                      contexto_gps=contexto_gps, context_map=context_map,
                      preview_data=preview_data)
        return True, "Previsualización abierta"
