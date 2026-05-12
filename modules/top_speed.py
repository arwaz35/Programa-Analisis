"""
Módulo de Velocidad Máxima.
Evalúa la velocidad máxima alcanzable por la motocicleta.
El piloto presiona la bocina al alcanzar la velocidad máxima y
mantiene la velocidad durante al menos 200 metros.

Soporta 1, 2 o 3 archivos CSV para análisis individual o comparativo.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pandas as pd

from modules.base_module import BaseModule
from utils.csv_parser import parse_csv, convert_units
from utils.event_detector import extract_topspeed_events, export_event_to_csv
from utils.metrics_calculator import calculate_topspeed_metrics, calculate_speed_difference
from utils.gps_utils import get_gps_context
from plotting.speed_plotter import plot_speed_comparison, plot_speed_detailed
from plotting.accel_plotter import plot_accel_vs_time
from plotting.rpm_plotter import plot_rpm_vs_time
from plotting.map_plotter import plot_gps_heatmap, plot_gps_route_simple
from config import RESULTADOS_DIR

# ══════════════════════════════════════════════════════════════════════
# MAPEO DE CELDAS EXCEL - Formato ft-nm-000-007.xlsx
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
    "comentarios": "A35",

    # --- Conditions ---
    "piloto_nombre": "B41",
    "piloto_peso": "B42",
    "piloto_altura": "B43",
    "piloto_foto": "B45",
    "pasajero_nombre": "J41",
    "pasajero_peso": "J42",
    "pasajero_altura": "J43",
    "pasajero_foto": "J45",
    "lugar_nombre": "W41",
    "lugar_altitud": "W42",
    "lugar_coordenadas": "W43",
    "lugar_link": "W44",
    "temp_ambiente": "AG41",
    "humedad": "AG42",
    "temp_suelo": "AG43",
    "mapa_trazado": "T46",

    # --- Velocidad Máxima: Tabla mejores eventos ---
    "topspeed_start_row": 70,
    "topspeed_col_num": "B",
    "topspeed_col_evento": "C",
    "topspeed_col_vi": "E",
    "topspeed_col_vf": "G",
    "topspeed_col_tiempo": "I",
    "topspeed_col_dist": "K",
    "topspeed_col_acel": "M",
    "topspeed_col_rpm": "O",
    "topspeed_img_resumen": "R66",

    # --- Best Event Velocidad Máxima ---
    "best_topspeed_vel_max": "B92",
    "best_topspeed_acel": "K92",
    "best_topspeed_rpm": "N92",
    "dashboard_speed": "E92",
    "speed_diff": "H92",
    "best_topspeed_img_vel": "R88",
    "best_topspeed_img_acel": "R100",
    "best_topspeed_img_rpm": "R106",
    "best_topspeed_img_mapa": "B94",
}

# Tamaños de imágenes para Excel (Alto cm, Ancho cm)
EXCEL_IMG_SIZES = {
    "mapa": (10.5, 15.5),
    "grafica_resumen": (11.5, 17.5),
    "grafica_vel": (7.0, 17.5),
    "grafica_small": (4.0, 17.5),
}


class TopSpeedModule(BaseModule):
    def build_ui(self):
        ctk.CTkLabel(self, text="Prueba de Velocidad Máxima",
                     font=("Arial", 16, "bold")).pack(pady=10)

        self.files_frame = ctk.CTkFrame(self)
        self.files_frame.pack(fill="x", padx=10, pady=5)

        # Filas de archivos
        self._create_file_row(self.files_frame, 1)
        self._create_file_row(self.files_frame, 2)
        self._create_file_row(self.files_frame, 3)

        # Campo de velocímetro del tablero
        dash_frame = ctk.CTkFrame(self)
        dash_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(dash_frame, text="Velocidad Tablero (km/h):",
                     font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.dashboard_speed_entry = ctk.CTkEntry(dash_frame, width=100,
                                                   placeholder_text="Ej: 110")
        self.dashboard_speed_entry.pack(side="left", padx=5)
        ctk.CTkLabel(dash_frame, text="(Lectura del velocímetro de la moto)",
                     font=("Arial", 10), text_color="gray").pack(side="left", padx=5)

        self.refresh_combos()

    def _create_file_row(self, parent, num):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(row, text=f"Archivo {num}:", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        moto_combo = ctk.CTkComboBox(row, values=["Seleccione Moto..."], width=150)
        moto_combo.pack(side="left", padx=5)

        pilot_combo = ctk.CTkComboBox(row, values=["Seleccione Piloto..."], width=130)
        pilot_combo.pack(side="left", padx=5)

        lugar_combo = ctk.CTkComboBox(row, values=["Seleccione Lugar..."], width=130)
        lugar_combo.pack(side="left", padx=5)

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

        for num in [1, 2, 3]:
            getattr(self, f'moto_combo_{num}').configure(values=moto_names)
            getattr(self, f'pilot_combo_{num}').configure(values=pilot_names)
            getattr(self, f'lugar_combo_{num}').configure(values=lugar_names)

    def get_data(self):
        """Retorna lista de inputs válidos."""
        inputs = []
        pilotos_data = self.data_handler.load_pilotos()
        motos_data = self.data_handler.load_motos()
        lugares_data = self.data_handler.load_lugares()

        for num in [1, 2, 3]:
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
        """Ejecuta el análisis de velocidad máxima."""
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
        """Procesa un solo archivo: Top 3 + mejor evento."""
        filepath = data['filepath']
        pilot = data['pilot']
        weight = data['weight']

        df = parse_csv(filepath)
        df = convert_units(df)

        raw_events = extract_topspeed_events(df, min_distance=200)
        valid_events = []
        for evt_df in raw_events:
            s_idx = evt_df.attrs.get('start_idx', evt_df.index[0])
            e_idx = evt_df.attrs.get('end_idx', evt_df.index[-1])

            m = calculate_topspeed_metrics(evt_df, s_idx, e_idx)
            if m:
                valid_events.append({
                    'df': evt_df, 'metrics': m, 'pilot': pilot,
                    'weight': weight, 'id': len(valid_events) + 1
                })

        if not valid_events:
            return False, "No se encontraron eventos válidos de velocidad máxima."

        # Ordenar por mayor velocidad máxima
        valid_events.sort(key=lambda x: x['metrics']['max_speed'], reverse=True)
        best = valid_events[0]
        top_3 = valid_events[:3]

        # Velocímetro del tablero
        dashboard_speed_str = self.dashboard_speed_entry.get()
        dashboard_speed = None
        speed_diff = None
        if dashboard_speed_str:
            try:
                dashboard_speed = float(dashboard_speed_str)
                speed_diff = calculate_speed_difference(best['metrics']['max_speed'], dashboard_speed)
            except ValueError:
                pass

        # --- CONSTRUIR DATOS DE PREVIEW ---
        contexto_gps = get_gps_context(df)

        max_dist = 0.0
        for ev in valid_events:
            m = ev.get('metrics')
            if m and m.get('dist_m', 0) > max_dist:
                max_dist = m['dist_m']
        if max_dist <= 0:
            max_dist = contexto_gps.get('distancia_m', 0.0)

        context_map = None
        context_map_buf = plot_gps_route_simple(best['df'], distance_m=max_dist)
        if context_map_buf:
            context_map = context_map_buf.getvalue()

        sections = []

        # Asignar display_name
        for i, ev in enumerate(top_3):
            ev['display_name'] = f"Event {ev['id']}"

        img_combined = plot_speed_comparison(top_3, "Top Speed - General Result")

        sections.append({
            "title": "Top Speed - Summary",
            "images": [{'bytes': img_combined.getvalue()}],
            "table_data": None
        })

        # Detalle del mejor evento
        img_detail_v = plot_speed_detailed(best, "Speed vs Time")
        img_detail_a = plot_accel_vs_time(best, "Acceleration vs Time")
        img_detail_rpm = plot_rpm_vs_time(best, "RPM vs Time") if 'RPM' in best['df'].columns else None
        img_detail_gps = plot_gps_heatmap(best, "Ubicación de la prueba")

        m = best['metrics']
        detail_info = f"Max Speed GPS: {m['max_speed']:.2f} km/h"
        if dashboard_speed is not None:
            detail_info += f" | Dashboard: {dashboard_speed:.1f} km/h | Diff: {speed_diff:.2f}%"

        tab_b = [["Max Speed GPS (km/h)", "Avg Acc (m/s²)", "Top RPM"],
                 [f"{m['max_speed']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"]]

        imgs_detalle = []
        if img_detail_gps:
            imgs_detalle.append({'bytes': img_detail_gps.getvalue()})
        imgs_detalle.append({'bytes': img_detail_v.getvalue()})
        if img_detail_rpm:
            imgs_detalle.append({'bytes': img_detail_rpm.getvalue()})
        imgs_detalle.append({'bytes': img_detail_a.getvalue()})

        sections.append({
            "title": f"Top Speed - Best Event ({pilot})\n{detail_info}",
            "images": imgs_detalle,
            "table_data": tab_b
        })

        preview_data = {
            "type": "topspeed",
            "moto_info": moto_data,
            "inputs": [{'pilot': pilot, 'weight': weight, 'altura': data.get('altura', '0')}],
            "comments": comments,
            "env_conditions": env_conditions,
            "sections": sections,
            "contexto_gps": contexto_gps,
            "context_map": context_map,
            "topspeed_data": {
                "top_3_events": top_3,
                "best_event": best,
                "dashboard_speed": dashboard_speed,
                "speed_diff": speed_diff,
                "img_combined": img_combined.getvalue(),
                "img_detail_v": img_detail_v.getvalue(),
                "img_detail_a": img_detail_a.getvalue(),
                "img_detail_rpm": img_detail_rpm.getvalue() if img_detail_rpm else None,
                "img_detail_gps": img_detail_gps.getvalue() if img_detail_gps else None,
            },
            "excel_cells": EXCEL_CELLS,
            "excel_img_sizes": EXCEL_IMG_SIZES,
        }

        from ui.preview_window import PreviewWindow

        def on_excel(p_data):
            from reports.excel_reporter import ExcelReporter
            try:
                r = ExcelReporter()
                ok, path = r.generate_topspeed(p_data)
                if ok:
                    messagebox.showinfo("Excel Guardado", f"Generado en:\n{path}")
                else:
                    messagebox.showerror("Excel Error", f"Error:\n{path}")
            except Exception as e:
                messagebox.showerror("Excel Exception", str(e))

        PreviewWindow(self, "Previsualización - Velocidad Máxima",
                      sections, on_excel_callback=on_excel,
                      contexto_gps=contexto_gps, context_map=context_map,
                      preview_data=preview_data)
        return True, "Previsualización abierta"

    def _process_comparison(self, inputs, moto_data, env_conditions, comments):
        """Procesa 2 o 3 archivos para comparación."""
        motos = [inp.get('moto_data', {}) for inp in inputs]
        lugares = [inp.get('lugar_data', {}) for inp in inputs]

        motos_same = all(m == motos[0] for m in motos)

        parsed_data = []
        for i, inp in enumerate(inputs):
            df = parse_csv(inp['filepath'])
            if df.empty:
                continue
            df = convert_units(df)

            raw_events = extract_topspeed_events(df, min_distance=200)
            valid_events = []
            for evt_df in raw_events:
                s_idx = evt_df.attrs.get('start_idx', evt_df.index[0])
                e_idx = evt_df.attrs.get('end_idx', evt_df.index[-1])
                m = calculate_topspeed_metrics(evt_df, s_idx, e_idx)
                if m:
                    valid_events.append({
                        'df': evt_df, 'metrics': m, 'pilot': inp['pilot'],
                        'weight': inp['weight'], 'id': len(valid_events) + 1
                    })

            if valid_events:
                valid_events.sort(key=lambda x: x['metrics']['max_speed'], reverse=True)

            if motos_same:
                d_name = lugares[i].get('Nombre', f"Event {i+1}")
            else:
                m_d = motos[i]
                d_name = f"{m_d.get('Nombre Comercial', '')} {m_d.get('Codigo', '')}".strip()
                if not d_name:
                    d_name = f"Event {i+1}"

            parsed_data.append({
                'df': df,
                'valid_events': valid_events,
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
            for ev in p['valid_events']:
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

        # Velocímetro del tablero
        dashboard_speed_str = self.dashboard_speed_entry.get()
        dashboard_speed = None
        speed_diff = None

        sections = []

        # Mejores de cada archivo
        best_all = []
        for p in parsed_data:
            if p['valid_events']:
                best_ev = p['valid_events'][0].copy()
                best_ev['display_name'] = p['display_name']
                best_ev['id'] = p['id']
                best_all.append(best_ev)

        if best_all:
            img_combined = plot_speed_comparison(best_all, "Top Speed - General Result")

            sections.append({
                "title": "Top Speed - Comparison",
                "images": [{'bytes': img_combined.getvalue()}],
                "table_data": None
            })

            # Detalle del archivo primario
            if primary['valid_events']:
                best = primary['valid_events'][0]

                if dashboard_speed_str:
                    try:
                        dashboard_speed = float(dashboard_speed_str)
                        speed_diff = calculate_speed_difference(best['metrics']['max_speed'], dashboard_speed)
                    except ValueError:
                        pass

                img_detail_v = plot_speed_detailed(best, "Speed vs Time")
                img_detail_a = plot_accel_vs_time(best, "Acceleration vs Time")
                img_detail_rpm = plot_rpm_vs_time(best, "RPM vs Time") if 'RPM' in primary['df'].columns else None
                img_detail_gps = plot_gps_heatmap(best, "Ubicación de la prueba")

                m = best['metrics']
                tab_b = [["Max Speed GPS (km/h)", "Avg Acc (m/s²)", "Top RPM"],
                         [f"{m['max_speed']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"]]

                imgs = []
                if img_detail_gps:
                    imgs.append({'bytes': img_detail_gps.getvalue()})
                imgs.append({'bytes': img_detail_v.getvalue()})
                if img_detail_rpm:
                    imgs.append({'bytes': img_detail_rpm.getvalue()})
                imgs.append({'bytes': img_detail_a.getvalue()})

                sections.append({
                    "title": "Top Speed - Best Event",
                    "images": imgs,
                    "table_data": tab_b
                })

        preview_data = {
            "type": "topspeed",
            "moto_info": primary['moto_data'],
            "inputs": inputs,
            "comments": comments,
            "env_conditions": env_conditions,
            "contexto_gps": contexto_gps,
            "context_map": context_map,
            "topspeed_data": {
                "top_3_events": best_all,
                "best_event": primary['valid_events'][0] if primary['valid_events'] else None,
                "dashboard_speed": dashboard_speed,
                "speed_diff": speed_diff,
                "img_combined": img_combined.getvalue() if best_all else None,
                "img_detail_v": img_detail_v.getvalue() if primary['valid_events'] else None,
                "img_detail_a": img_detail_a.getvalue() if primary['valid_events'] else None,
                "img_detail_rpm": img_detail_rpm.getvalue() if primary['valid_events'] and img_detail_rpm else None,
                "img_detail_gps": img_detail_gps.getvalue() if primary['valid_events'] and img_detail_gps else None,
            },
            "excel_cells": EXCEL_CELLS,
            "excel_img_sizes": EXCEL_IMG_SIZES,
        }

        from ui.preview_window import PreviewWindow

        def on_excel(p_data):
            from reports.excel_reporter import ExcelReporter
            try:
                r = ExcelReporter()
                ok, path = r.generate_topspeed(p_data)
                if ok:
                    messagebox.showinfo("Excel Guardado", f"Generado en:\n{path}")
                else:
                    messagebox.showerror("Excel Error", f"Error:\n{path}")
            except Exception as e:
                messagebox.showerror("Excel Exception", str(e))

        PreviewWindow(self, "Previsualización Comparativa - Velocidad Máxima",
                      sections, on_excel_callback=on_excel,
                      contexto_gps=contexto_gps, context_map=context_map,
                      preview_data=preview_data)

        return True, "Análisis comparativo procesado correctamente"
