"""
Módulo de Frenado.
Incluye análisis de frenado 40→0 y 60→0 km/h.

Soporta 1, 2 o 3 archivos CSV para análisis individual o comparativo.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pandas as pd

from modules.base_module import BaseModule
from utils.csv_parser import parse_csv, convert_units
from utils.event_detector import (extract_braking_events, refine_braking_start,
                                   export_event_to_csv)
from utils.metrics_calculator import calculate_braking_metrics
from utils.gps_utils import get_gps_context
from plotting.speed_plotter import plot_speed_comparison, plot_speed_detailed
from plotting.accel_plotter import plot_accel_vs_time
from plotting.rpm_plotter import plot_rpm_vs_time
from plotting.map_plotter import plot_gps_heatmap, plot_gps_route_simple
from config import RESULTADOS_DIR

# ══════════════════════════════════════════════════════════════════════
# MAPEO DE CELDAS EXCEL - Formato ft-nm-000-005.xlsx
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
    "comentarios": "A37",

    # --- Conditions ---
    "piloto_nombre": "B43",
    "piloto_peso": "B44",
    "piloto_altura": "B45",
    "piloto_foto": "B47",
    "pasajero_nombre": "J43",
    "pasajero_peso": "J44",
    "pasajero_altura": "J45",
    "pasajero_foto": "J47",
    "lugar_nombre": "W43",
    "lugar_altitud": "W44",
    "lugar_coordenadas": "W45",
    "lugar_link": "W46",
    "temp_ambiente": "AG43",
    "humedad": "AG44",
    "temp_suelo": "AG45",
    "mapa_trazado": "T48",

    # --- Frenado 40→0: Tabla mejores eventos ---
    "brake40_start_row": 72,
    "brake40_col_num": "B",
    "brake40_col_evento": "C",
    "brake40_col_vi": "E",
    "brake40_col_vf": "G",
    "brake40_col_tiempo": "I",
    "brake40_col_dist": "K",
    "brake40_col_acel": "M",
    "brake40_col_rpm": "O",
    "brake40_img_resumen": "R68",

    # --- Frenado 60→0: Tabla mejores eventos ---
    "brake60_start_row": 92,
    "brake60_col_num": "B",
    "brake60_col_evento": "C",
    "brake60_col_vi": "E",
    "brake60_col_vf": "G",
    "brake60_col_tiempo": "I",
    "brake60_col_dist": "K",
    "brake60_col_acel": "M",
    "brake60_col_rpm": "O",
    "brake60_img_resumen": "R88",

    # --- Best Event Frenado 40→0 ---
    "best_brake40_row": 114,
    "best_brake40_img_vel": "R110",
    "best_brake40_img_acel": "R122",
    "best_brake40_img_rpm": "R128",
    "best_brake40_img_mapa": "B116",

    # --- Best Event Frenado 60→0 ---
    "best_brake60_row": 139,
    "best_brake60_img_vel": "R135",
    "best_brake60_img_acel": "R147",
    "best_brake60_img_rpm": "R153",
    "best_brake60_img_mapa": "B141",
}

# Tamaños de imágenes para Excel (Alto cm, Ancho cm)
EXCEL_IMG_SIZES = {
    "mapa": (10.5, 15.5),
    "grafica_resumen": (11.5, 17.5),
    "grafica_vel": (7.0, 17.5),
    "grafica_small": (4.0, 17.5),
}

# Velocidades fijas de frenado
BRAKING_SPEEDS = [40, 60]


class BrakingModule(BaseModule):
    def build_ui(self):
        ctk.CTkLabel(self, text="Prueba de Frenado",
                     font=("Arial", 16, "bold")).pack(pady=10)

        self.files_frame = ctk.CTkFrame(self)
        self.files_frame.pack(fill="x", padx=10, pady=5)

        self.file_numbers = [1] if getattr(self, 'mode', 'individual') == 'individual' else [1, 2, 3]

        for num in self.file_numbers:
            self._create_file_row(self.files_frame, num)

        self.refresh_combos()

    def _create_file_row(self, parent, num):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=5, pady=5)

        label_text = f"Archivo {num}:" if len(self.file_numbers) > 1 else "Archivo CSV:"
        ctk.CTkLabel(row, text=label_text, font=("Arial", 12, "bold")).pack(side="left", padx=5)

        # Moto combo
        moto_combo = ctk.CTkComboBox(row, values=["Seleccione Moto..."], width=150)
        moto_combo.pack(side="left", padx=5)

        # Piloto combo
        pilot_combo = ctk.CTkComboBox(row, values=["Seleccione Piloto..."], width=130)
        pilot_combo.pack(side="left", padx=5)

        # Lugar combo
        lugar_combo = ctk.CTkComboBox(row, values=["Seleccione Lugar..."], width=130)
        lugar_combo.pack(side="left", padx=5)

        # Ruta del archivo
        path_entry = ctk.CTkEntry(row, width=150, placeholder_text="Ruta del archivo CSV...")
        path_entry.pack(side="left", padx=5, fill="x", expand=True)

        def browse():
            f = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")])
            if f:
                path_entry.delete(0, "end")
                path_entry.insert(0, f)

        ctk.CTkButton(row, text="Buscar", width=60, command=browse).pack(side="left", padx=5)

        # Almacenar referencias
        setattr(self, f'moto_combo_{num}', moto_combo)
        setattr(self, f'pilot_combo_{num}', pilot_combo)
        setattr(self, f'lugar_combo_{num}', lugar_combo)
        setattr(self, f'path_entry_{num}', path_entry)

    def refresh_combos(self):
        """Actualiza las listas de motos y pilotos."""
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

        for num in getattr(self, 'file_numbers', [1]):
            getattr(self, f'moto_combo_{num}').configure(values=moto_names)
            getattr(self, f'pilot_combo_{num}').configure(values=pilot_names)
            getattr(self, f'lugar_combo_{num}').configure(values=lugar_names)

    def get_data(self):
        """Retorna lista de inputs válidos."""
        inputs = []
        pilotos_data = self.data_handler.load_pilotos()
        motos_data = self.data_handler.load_motos()
        lugares_data = self.data_handler.load_lugares()

        for num in getattr(self, 'file_numbers', [1]):
            path = getattr(self, f'path_entry_{num}').get()
            pilot = getattr(self, f'pilot_combo_{num}').get()
            moto_str = getattr(self, f'moto_combo_{num}').get()
            lugar_str = getattr(self, f'lugar_combo_{num}').get()

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

            lugar_data = {}
            for l in lugares_data:
                if l.get('Nombre', '') == lugar_str:
                    lugar_data = l
                    break
            else:
                lugar_data = {'Nombre': lugar_str}

            inputs.append({
                'filepath': path,
                'pilot': pilot,
                'weight': str(weight),
                'altura': str(altura),
                'moto_data': moto_data,
                'lugar_data': lugar_data
            })

        return inputs

    def process(self, moto_data, env_conditions, comments):
        """Ejecuta el análisis de frenado."""
        valid_inputs = self.get_data()

        if not valid_inputs:
            messagebox.showerror("Error", "Debe seleccionar al menos un archivo válido con piloto.")
            return False, "Sin entradas válidas"

        try:
            if len(valid_inputs) == 1:
                return self._process_single(valid_inputs[0], moto_data, env_conditions, comments)
            else:
                return self._process_comparison(valid_inputs, moto_data, env_conditions, comments)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error en análisis: {str(e)}"

    def _process_single(self, data, moto_data, env_conditions, comments):
        """Procesa un solo archivo: Top 3 + mejor evento para cada velocidad de frenado."""
        filepath = data['filepath']
        pilot = data['pilot']
        weight = data['weight']

        df = parse_csv(filepath)
        df = convert_units(df)

        # --- FRENADO POR CADA VELOCIDAD ---
        braking_results = {}
        for from_speed in BRAKING_SPEEDS:
            raw_events = extract_braking_events(df, from_speed=from_speed)
            valid_events = []
            for evt_df in raw_events:
                s_idx = refine_braking_start(evt_df, from_speed)
                # Buscar el punto donde v < 1
                stopped = evt_df.loc[s_idx:][evt_df.loc[s_idx:, 'Velocidad_GPS'] < 1.0]
                if stopped.empty:
                    continue
                e_idx = stopped.index[0]

                m = calculate_braking_metrics(evt_df, s_idx, e_idx)
                if m:
                    # Validar que la velocidad inicial real esté dentro del rango objetivo +- 5 km/h
                    if (from_speed - 5) <= m['v_start'] <= (from_speed + 5):
                        valid_events.append({
                            'df': evt_df, 'metrics': m, 'pilot': pilot,
                            'weight': weight, 'id': len(valid_events) + 1
                        })

            if valid_events:
                # Ordenar por menor distancia de frenado (mejor = menos distancia)
                valid_events.sort(key=lambda x: x['metrics']['dist_m'])
                braking_results[from_speed] = {
                    'best': valid_events[0],
                    'top_3': valid_events[:3]
                }

        if not braking_results:
            return False, "No se encontraron eventos válidos de frenado."

        # --- CONSTRUIR DATOS DE PREVIEW ---
        contexto_gps = get_gps_context(df)

        # Calcular distancia de la pista
        max_dist = 0.0
        for spd, res in braking_results.items():
            for ev in res['top_3']:
                m = ev.get('metrics')
                if m and m.get('dist_m', 0) > max_dist:
                    max_dist = m['dist_m']
        if max_dist <= 0:
            max_dist = contexto_gps.get('distancia_m', 0.0)

        context_map = None
        first_best = list(braking_results.values())[0]['best']
        context_map_buf = plot_gps_route_simple(first_best['df'], distance_m=max_dist)
        if context_map_buf:
            context_map = context_map_buf.getvalue()

        sections = []
        preview_data = {
            "type": "braking",
            "moto_info": moto_data,
            "inputs": [{'pilot': pilot, 'weight': weight, 'altura': data.get('altura', '0')}],
            "comments": comments,
            "env_conditions": env_conditions,
            "sections": sections,
            "contexto_gps": contexto_gps,
            "context_map": context_map,
            "braking_data": {},
            "excel_cells": EXCEL_CELLS,
            "excel_img_sizes": EXCEL_IMG_SIZES,
        }

        for from_speed in BRAKING_SPEEDS:
            if from_speed not in braking_results:
                continue

            res = braking_results[from_speed]
            top_3 = res['top_3']
            best = res['best']

            # Asignar display_name
            for i, ev in enumerate(top_3):
                ev['display_name'] = f"Event {ev['id']}"

            # Gráfica comparativa de top 3
            img_combined = plot_speed_comparison(top_3, f"Braking {from_speed}→0 - General Result")

            sections.append({
                "title": f"Braking {from_speed}→0 km/h - Summary",
                "images": [{'bytes': img_combined.getvalue()}],
                "table_data": None
            })

            # Detalle del mejor evento
            img_detail_v = plot_speed_detailed(best, "Speed vs Time")
            img_detail_a = plot_accel_vs_time(best, "Deceleration vs Time")
            img_detail_rpm = plot_rpm_vs_time(best, "RPM vs Time") if 'RPM' in best['df'].columns else None
            img_detail_gps = plot_gps_heatmap(best, "Ubicación de la prueba")

            imgs_detalle = []
            if img_detail_gps:
                imgs_detalle.append({'bytes': img_detail_gps.getvalue()})
            imgs_detalle.append({'bytes': img_detail_v.getvalue()})
            if img_detail_rpm:
                imgs_detalle.append({'bytes': img_detail_rpm.getvalue()})
            imgs_detalle.append({'bytes': img_detail_a.getvalue()})

            m = best['metrics']
            tab_b = [["V. Start (km/h)", "V. End (km/h)", "Time (s)", "Distance (m)", "Avg Decel (m/s²)", "Top RPM"],
                     [f"{m['v_start']:.2f}", f"{m['v_final']:.2f}", f"{m['time_s']:.2f}",
                      f"{m['dist_m']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"]]

            sections.append({
                "title": f"Braking {from_speed}→0 km/h - Best Event ({pilot})",
                "images": imgs_detalle,
                "table_data": tab_b
            })

            preview_data["braking_data"][from_speed] = {
                "top_3_events": top_3,
                "best_event": best,
                "img_combined": img_combined.getvalue(),
                "img_detail_v": img_detail_v.getvalue(),
                "img_detail_a": img_detail_a.getvalue(),
                "img_detail_rpm": img_detail_rpm.getvalue() if img_detail_rpm else None,
                "img_detail_gps": img_detail_gps.getvalue() if img_detail_gps else None,
            }

        # Abrir previsualización
        from ui.preview_window import PreviewWindow

        def on_excel(p_data):
            from reports.excel_reporter import ExcelReporter
            try:
                r = ExcelReporter()
                ok, path = r.generate_braking(p_data)
                if ok:
                    messagebox.showinfo("Excel Guardado", f"Generado en:\n{path}")
                else:
                    messagebox.showerror("Excel Error", f"Error:\n{path}")
            except Exception as e:
                messagebox.showerror("Excel Exception", str(e))

        PreviewWindow(self, "Previsualización - Frenado",
                      sections, on_excel_callback=on_excel,
                      contexto_gps=contexto_gps, context_map=context_map,
                      preview_data=preview_data)
        return True, "Previsualización abierta"

    def _process_comparison(self, inputs, moto_data, env_conditions, comments):
        """Procesa 2 o 3 archivos para comparación."""
        motos = [inp.get('moto_data', {}) for inp in inputs]
        lugares = [inp.get('lugar_data', {}) for inp in inputs]
        pilots = [inp.get('pilot', '') for inp in inputs]

        motos_same = all(m == motos[0] for m in motos)
        lugares_same = all(l == lugares[0] for l in lugares)
        pilots_same = all(p == pilots[0] for p in pilots)

        parsed_data = []
        for i, inp in enumerate(inputs):
            df = parse_csv(inp['filepath'])
            if df.empty:
                continue
            df = convert_units(df)

            braking_results = {}
            for from_speed in BRAKING_SPEEDS:
                raw_events = extract_braking_events(df, from_speed=from_speed)
                valid_events = []
                for evt_df in raw_events:
                    s_idx = refine_braking_start(evt_df, from_speed)
                    stopped = evt_df.loc[s_idx:][evt_df.loc[s_idx:, 'Velocidad_GPS'] < 1.0]
                    if stopped.empty:
                        continue
                    e_idx = stopped.index[0]
                    m = calculate_braking_metrics(evt_df, s_idx, e_idx)
                    if m:
                        # Validar que la velocidad inicial real esté dentro del rango objetivo +- 5 km/h
                        if (from_speed - 5) <= m['v_start'] <= (from_speed + 5):
                            valid_events.append({
                                'df': evt_df, 'metrics': m, 'pilot': inp['pilot'],
                                'weight': inp['weight'], 'id': len(valid_events) + 1
                            })
                if valid_events:
                    valid_events.sort(key=lambda x: x['metrics']['dist_m'])
                    braking_results[from_speed] = {
                        'best': valid_events[0],
                        'top_3': valid_events[:3]
                    }

            if not motos_same:
                m = motos[i]
                d_name = m.get('Código Modelo') or m.get('Codigo') or m.get('Nombre Comercial', f"Moto {i+1}")
            elif not pilots_same:
                d_name = pilots[i]
            elif not lugares_same:
                d_name = lugares[i].get('Nombre', f"Lugar {i+1}")
            else:
                d_name = f"Pasada {i+1}"

            parsed_data.append({
                'df': df,
                'braking_results': braking_results,
                'pilot': inp['pilot'],
                'moto_data': motos[i],
                'lugar_data': lugares[i],
                'display_name': d_name,
                'id': i + 1
            })

        if not parsed_data:
            return False, "No se encontraron datos válidos en los archivos."

        primary = parsed_data[0]
        contexto_gps = get_gps_context(primary['df'])

        max_dist = 0.0
        for p in parsed_data:
            for spd, res in p['braking_results'].items():
                for ev in res['top_3']:
                    m = ev.get('metrics')
                    if m and m.get('dist_m', 0) > max_dist:
                        max_dist = m['dist_m']
        if max_dist <= 0:
            max_dist = contexto_gps.get('distancia_m', 0.0)

        context_map = None
        if max_dist > 0:
            context_map_buf = plot_gps_route_simple(primary['df'], distance_m=max_dist)
            if context_map_buf:
                context_map = context_map_buf.getvalue()

        preview_data = {
            "type": "braking",
            "moto_info": primary['moto_data'],
            "inputs": inputs,
            "comments": comments,
            "env_conditions": env_conditions,
            "contexto_gps": contexto_gps,
            "context_map": context_map,
            "braking_data": {},
            "excel_cells": EXCEL_CELLS,
            "excel_img_sizes": EXCEL_IMG_SIZES,
        }

        sections = []

        for from_speed in BRAKING_SPEEDS:
            # Mejores de cada archivo
            best_all = []
            for p in parsed_data:
                if from_speed in p['braking_results']:
                    best_ev = p['braking_results'][from_speed]['best'].copy()
                    best_ev['display_name'] = p['display_name']
                    best_ev['id'] = p['id']
                    best_all.append(best_ev)

            if best_all:
                img_combined = plot_speed_comparison(best_all, f"Braking {from_speed}→0 - Comparison")

                table_b = [["Event", "V. Start (km/h)", "V. End (km/h)", "Time (s)", "Distance (m)", "Avg Decel (m/s²)", "Top RPM"]]
                for ev in best_all:
                    m = ev['metrics']
                    table_b.append([
                        ev.get('display_name', f"Event {ev.get('id', '')}"),
                        f"{m['v_start']:.2f}",
                        f"{m['v_final']:.2f}",
                        f"{m['time_s']:.2f}",
                        f"{m['dist_m']:.2f}",
                        f"{m['avg_acc']:.2f}",
                        f"{int(m['top_rpm'])}"
                    ])

                sections.append({
                    "title": f"Braking {from_speed}→0 km/h - Comparison",
                    "images": [{'bytes': img_combined.getvalue()}],
                    "table_data": table_b
                })

                preview_data["braking_data"][from_speed] = {
                    "top_3_events": best_all,
                    "img_combined": img_combined.getvalue(),
                    "best_event": None,
                }

        from ui.preview_window import PreviewWindow

        def on_excel(p_data):
            from reports.excel_reporter import ExcelReporter
            try:
                r = ExcelReporter()
                ok, path = r.generate_braking(p_data)
                if ok:
                    messagebox.showinfo("Excel Guardado", f"Generado en:\n{path}")
                else:
                    messagebox.showerror("Excel Error", f"Error:\n{path}")
            except Exception as e:
                messagebox.showerror("Excel Exception", str(e))

        PreviewWindow(self, "Previsualización Comparativa - Frenado",
                      sections, on_excel_callback=on_excel,
                      contexto_gps=contexto_gps, context_map=context_map,
                      preview_data=preview_data)

        return True, "Análisis comparativo procesado correctamente"
