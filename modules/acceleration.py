"""
Módulo de Aceleración y Recuperación.
Incluye análisis 0-80 km/h y recuperación desde 30, 40, 50 km/h.

Soporta 1 o 2 archivos CSV para análisis individual o comparativo.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pandas as pd

from modules.base_module import BaseModule
from utils.csv_parser import parse_csv, convert_units
from utils.event_detector import (extract_acceleration_events, extract_recovery_events,
                                   refine_acceleration_start, export_event_to_csv)
from utils.metrics_calculator import (calculate_acceleration_metrics,
                                       calculate_recovery_metrics, calculate_segments)
from utils.gps_utils import get_gps_context
from plotting.speed_plotter import plot_speed_comparison, plot_speed_detailed
from plotting.accel_plotter import plot_accel_vs_time
from plotting.rpm_plotter import plot_rpm_vs_time
from plotting.map_plotter import plot_gps_heatmap, plot_gps_route_simple
from config import ACCEL_BENCHMARKS, RESULTADOS_DIR, MAX_SPEED_DROP_KMH

# ══════════════════════════════════════════════════════════════════════
# MAPEO DE CELDAS EXCEL - Formato ft-nm-000-008.xlsx
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
    "comentarios": "A40",

    # --- Conditions ---
    "piloto_nombre": "B46",
    "piloto_peso": "B47",
    "piloto_altura": "B48",
    "piloto_foto": "B50",
    "pasajero_nombre": "J46",
    "pasajero_peso": "J47",
    "pasajero_altura": "J48",
    "pasajero_foto": "J50",
    "lugar_nombre": "W46",
    "lugar_altitud": "W47",
    "lugar_coordenadas": "W48",
    "lugar_link": "W49",
    "temp_ambiente": "AG46",
    "humedad": "AG47",
    "temp_suelo": "AG48",
    "mapa_trazado": "T51",

    # --- Aceleración 0-80: Tabla mejores eventos ---
    "accel_start_row": 75,
    "accel_col_num": "B",
    "accel_col_evento": "C",
    "accel_col_vi": "E",
    "accel_col_vf": "G",
    "accel_col_tiempo": "I",
    "accel_col_dist": "K",
    "accel_col_acel": "M",
    "accel_col_rpm": "O",
    "accel_img_resumen": "R71",

    # --- Recuperación: Tabla mejores eventos ---
    "rec_start_row": 95,
    "rec_col_num": "B",
    "rec_col_evento": "C",
    "rec_col_vi": "E",
    "rec_col_vf": "G",
    "rec_col_tiempo": "I",
    "rec_col_dist": "K",
    "rec_col_acel": "M",
    "rec_col_rpm": "O",
    "rec_img_resumen": "R91",

    # --- Best Event Aceleración 0-80: Segmentos ---
    "seg_start_row": 117,
    "seg_col_name": "B",
    "seg_col_time": "E",
    "seg_col_dist": "H",
    "seg_col_acc": "K",
    "seg_col_rpm": "N",
    "best_accel_img_vel": "R113",
    "best_accel_img_acel": "R125",
    "best_accel_img_rpm": "R131",
    "best_accel_img_mapa": "B123",

    # --- Best Event Recuperación 30-80 ---
    "best_rec30_row": 142,
    "best_rec30_img_vel": "R138",
    "best_rec30_img_acel": "R150",
    "best_rec30_img_rpm": "R156",
    "best_rec30_img_mapa": "B144",

    # --- Best Event Recuperación 40-80 ---
    "best_rec40_row": 167,
    "best_rec40_img_vel": "R163",
    "best_rec40_img_acel": "R175",
    "best_rec40_img_rpm": "R181",
    "best_rec40_img_mapa": "B169",

    # --- Best Event Recuperación 50-80 ---
    "best_rec50_row": 192,
    "best_rec50_img_vel": "R188",
    "best_rec50_img_acel": "R200",
    "best_rec50_img_rpm": "R206",
    "best_rec50_img_mapa": "B194",
}

# Tamaños de imágenes para Excel (Alto cm, Ancho cm)
EXCEL_IMG_SIZES = {
    "mapa": (10.5, 15.5),
    "grafica_resumen": (11.5, 17.5),
    "grafica_vel": (7.0, 17.5),
    "grafica_small": (4.0, 17.5),
}


class AccelerationModule(BaseModule):
    """Módulo completo de Aceleración y Recuperación."""

    def build_ui(self):
        ctk.CTkLabel(self, text="Prueba de Aceleración y Recuperación",
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

            # Buscar datos de moto
            moto_data = {}
            for m in motos_data:
                check = f"{m.get('Nombre Comercial', '')} - {m.get('Placa', '')}"
                if check == moto_str:
                    moto_data = m
                    break

            # Buscar datos del lugar
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
        """Ejecuta el análisis de aceleración y recuperación."""
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

        lugar_name = env_conditions.get('lugar', {}).get('Nombre', 'SinLugar') if env_conditions else 'SinLugar'

        try:
            target_speed = float(moto_data.get('Velocidad Tope (km/h)') or 80)
        except (ValueError, TypeError):
            target_speed = 80.0

        accel_benchmarks = [v for v in range(0, int(target_speed) + 1, 20)]
        if accel_benchmarks[-1] < target_speed:
            accel_benchmarks.append(int(target_speed))

        # --- ACELERACIÓN 0-TOPE ---
        raw_accel = extract_acceleration_events(df, target_speed=target_speed)
        valid_accel = []
        seen_starts = set()
        for evt_df in raw_accel:
            s_idx = refine_acceleration_start(evt_df)
            if s_idx in seen_starts:
                continue
            seen_starts.add(s_idx)

            ref_loc = evt_df.index.get_loc(s_idx)
            new_slice_start = max(0, ref_loc - 20)
            trimmed_df = evt_df.iloc[new_slice_start:].copy()
            trimmed_df.attrs = evt_df.attrs.copy()
            trimmed_df.attrs['start_idx'] = s_idx

            m = calculate_acceleration_metrics(trimmed_df, s_idx, target_speed=target_speed)
            if m:
                # Validar continuidad de aceleración (sin caídas >= MAX_SPEED_DROP_KMH)
                phase_v = trimmed_df.loc[s_idx:m['end_idx'], 'Velocidad_GPS']
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

                v_s = trimmed_df.loc[s_idx, 'Velocidad_GPS']
                if v_s < 5.0:  # Confirmar inicio desde ~0
                    valid_accel.append({
                        'df': trimmed_df, 'metrics': m, 'pilot': pilot,
                        'weight': weight, 'id': len(valid_accel) + 1
                    })

        if valid_accel:
            valid_accel.sort(key=lambda x: x['metrics']['time_s'])
            best_accel = valid_accel[0]
            top_3_accel = valid_accel[:3]
        else:
            best_accel, top_3_accel = None, []

        # --- RECUPERACIÓN 30, 40, 50 ---
        raw_rec = extract_recovery_events(df, target_speed=target_speed)
        valid_rec = []
        for evt_df in raw_rec:
            m = calculate_recovery_metrics(evt_df)
            if m:
                valid_rec.append({
                    'df': evt_df, 'metrics': m,
                    'group': evt_df.attrs.get('group'),
                    'pilot': pilot, 'weight': weight, 'id': len(valid_rec) + 1
                })

        recovery_results = {}
        if valid_rec:
            groups = {30: [], 40: [], 50: []}
            for v in valid_rec:
                g = v['group']
                if g in groups:
                    groups[g].append(v)

            for g, evs in groups.items():
                if not evs:
                    continue
                evs.sort(key=lambda x: x['metrics']['time_s'])
                recovery_results[g] = {'best': evs[0], 'top_3': evs[:3]}

        if not best_accel and not recovery_results:
            return False, "No se encontraron eventos válidos de Aceleración ni Recuperación."

        # --- CONSTRUIR DATOS DE PREVIEW ---
        contexto_gps = get_gps_context(df)

        # Calcular distancia de la pista: buscar el evento con el recorrido más largo
        all_events_for_dist = []
        if valid_accel:
            all_events_for_dist.extend(valid_accel)
        if valid_rec:
            all_events_for_dist.extend(valid_rec)

        max_dist = 0.0
        for ev in all_events_for_dist:
            m = ev.get('metrics')
            if m and m.get('dist_m', 0) > max_dist:
                max_dist = m['dist_m']

        # Si no hay eventos con distancia válida, usar la del contexto GPS
        if max_dist <= 0:
            max_dist = contexto_gps.get('distancia_m', 0.0)

        dist_total = max_dist

        # Mapa contexto
        context_map = None
        target_df_for_map = best_accel['df'] if best_accel else (valid_rec[0]['df'] if valid_rec else df)
        if target_df_for_map is not None:
            context_map_buf = plot_gps_route_simple(target_df_for_map, distance_m=dist_total)
            if context_map_buf:
                context_map = context_map_buf.getvalue()

        sections = []
        preview_data = {
            "type": "accel_recovery",
            "moto_info": moto_data,
            "inputs": [{'pilot': pilot, 'weight': weight, 'altura': data.get('altura', '0')}],
            "comments": comments,
            "env_conditions": env_conditions,
            "sections": sections,
            "contexto_gps": contexto_gps,
            "context_map": context_map,
            "accel_data": None,
            "recovery_data": None,
            "excel_cells": EXCEL_CELLS,
            "excel_img_sizes": EXCEL_IMG_SIZES,
        }

        # --- SECCIONES ACELERACIÓN ---
        if best_accel:
            img_combined = plot_speed_comparison(top_3_accel, f"Acceleration 0-{int(target_speed)} - General Result")
            img_detail_v = plot_speed_detailed(best_accel, "Speed vs Time", benchmarks=accel_benchmarks)
            img_detail_a = plot_accel_vs_time(best_accel, "Acceleration vs Time", benchmarks=accel_benchmarks)
            img_detail_rpm = plot_rpm_vs_time(best_accel, "RPM vs Time", benchmarks=accel_benchmarks) if 'RPM' in best_accel['df'].columns else None
            img_detail_gps = plot_gps_heatmap(best_accel, "Ubicación de la prueba")

            segments = calculate_segments(best_accel['df'], best_accel['metrics']['start_idx'], accel_benchmarks)
            # Agregar fila total
            bm = best_accel['metrics']
            segments.append([f"0-{int(target_speed)}", f"{bm['time_s']:.2f}", f"{bm['dist_m']:.2f}", f"{bm['avg_acc']:.2f}", f"{int(bm['top_rpm'])}"])

            sections.append({
                "title": f"Acceleration 0-{int(target_speed)} km/h - Summary",
                "images": [{'bytes': img_combined.getvalue()}],
                "table_data": None
            })

            imgs_detalle = []
            if img_detail_gps:
                imgs_detalle.append({'bytes': img_detail_gps.getvalue()})
            imgs_detalle.append({'bytes': img_detail_v.getvalue()})
            if img_detail_rpm:
                imgs_detalle.append({'bytes': img_detail_rpm.getvalue()})
            imgs_detalle.append({'bytes': img_detail_a.getvalue()})

            sections.append({
                "title": f"Acceleration 0-{int(target_speed)} - Best Event ({best_accel['pilot']})",
                "images": imgs_detalle,
                "table_data": [["Segment (km/h)", "Time (s)", "Distance (m)", "Avg Acc (m/s²)", "Top RPM"]] + segments
            })

            preview_data["accel_data"] = {
                "top_3_events": top_3_accel,
                "segments": segments,
                "img_combined": img_combined.getvalue(),
                "img_detail_v": img_detail_v.getvalue(),
                "img_detail_a": img_detail_a.getvalue(),
                "img_detail_rpm": img_detail_rpm.getvalue() if img_detail_rpm else None,
                "img_detail_gps": img_detail_gps.getvalue() if img_detail_gps else None,
            }

        # --- SECCIONES RECUPERACIÓN ---
        if recovery_results:
            all_rec_tops = []
            best_of_each = []
            for g in [30, 40, 50]:
                if g in recovery_results:
                    all_rec_tops.extend(recovery_results[g]['top_3'])
                    best_of_each.append(recovery_results[g]['best'])

            img_combined_rec = plot_speed_comparison(all_rec_tops, f"Acceleration 30-{int(target_speed)}, 40-{int(target_speed)}, 50-{int(target_speed)} - General Result")

            table_r = [["V. Start (km/h)", "V. End (km/h)", "Time (s)", "Distance (m)", "Avg Acc (m/s²)", "Top RPM"]]
            for ev in best_of_each:
                m = ev['metrics']
                table_r.append([f"{m['v_start']:.2f}", f"{m['v_final']:.2f}", f"{m['time_s']:.2f}",
                                f"{m['dist_m']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"])

            sections.append({
                "title": f"Recovery - General Summary (up to {int(target_speed)} km/h)",
                "images": [{'bytes': img_combined_rec.getvalue()}],
                "table_data": table_r
            })

            preview_data["recovery_data"] = {
                "summary_img": img_combined_rec.getvalue(),
                "summary_events": all_rec_tops,
                "bands": {}
            }

            for g in [30, 40, 50]:
                if g in recovery_results:
                    b = recovery_results[g]['best']
                    img_v = plot_speed_comparison([b], f"Speed vs Time ({g}-{int(target_speed)})")
                    img_a = plot_accel_vs_time(b, f"Acceleration vs Time ({g}-{int(target_speed)})")
                    img_rpm = plot_rpm_vs_time(b, f"RPM vs Time ({g}-{int(target_speed)})") if 'RPM' in b['df'].columns else None
                    img_gps = plot_gps_heatmap(b, "Ubicación de la prueba")

                    m = b['metrics']
                    tab_b = [["V. Start", "V. End", "Time", "Distance", "Avg Acc", "Top RPM"],
                             [f"{m['v_start']:.2f}", f"{m['v_final']:.2f}", f"{m['time_s']:.2f}",
                              f"{m['dist_m']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"]]

                    imgs = []
                    if img_gps:
                        imgs.append({'bytes': img_gps.getvalue()})
                    imgs.append({'bytes': img_v.getvalue()})
                    if img_rpm:
                        imgs.append({'bytes': img_rpm.getvalue()})
                    imgs.append({'bytes': img_a.getvalue()})

                    sections.append({
                        "title": f"Recovery {g}-{int(target_speed)} km/h - Best Event",
                        "images": imgs,
                        "table_data": tab_b
                    })

                    preview_data["recovery_data"]["bands"][g] = {
                        "best_event": b,
                        "img_v": img_v.getvalue(),
                        "img_a": img_a.getvalue(),
                        "img_rpm": img_rpm.getvalue() if img_rpm else None,
                        "img_gps": img_gps.getvalue() if img_gps else None,
                    }

        # Abrir previsualización
        from ui.preview_window import PreviewWindow

        def on_excel(p_data):
            from reports.excel_reporter import ExcelReporter
            try:
                r = ExcelReporter()
                ok, path = r.generate_accel_recovery(p_data)
                if ok:
                    messagebox.showinfo("Excel Guardado", f"Generado en:\n{path}")
                else:
                    messagebox.showerror("Excel Error", f"Error:\n{path}")
            except Exception as e:
                messagebox.showerror("Excel Exception", str(e))

        PreviewWindow(self, "Previsualización - Aceleración y Recuperación",
                      sections, on_excel_callback=on_excel,
                      contexto_gps=contexto_gps, context_map=context_map,
                      preview_data=preview_data)
        return True, "Previsualización abierta"

    def _process_comparison(self, inputs, moto_data, env_conditions, comments):
        """Procesa 2 o 3 archivos para comparación."""
        from utils.csv_parser import parse_csv, convert_units
        from utils.event_detector import extract_acceleration_events, extract_recovery_events, refine_acceleration_start
        from utils.metrics_calculator import calculate_acceleration_metrics, calculate_recovery_metrics
        from utils.gps_utils import get_gps_context
        from plotting.speed_plotter import plot_speed_comparison, plot_speed_detailed
        from plotting.accel_plotter import plot_accel_vs_time
        from plotting.rpm_plotter import plot_rpm_vs_time
        from plotting.map_plotter import plot_gps_heatmap, plot_gps_route_simple

        # 1. Lógica de Nombres
        motos = [inp.get('moto_data', {}) for inp in inputs]
        lugares = [inp.get('lugar_data', {}) for inp in inputs]
        pilots = [inp.get('pilot', '') for inp in inputs]

        motos_same = all(m == motos[0] for m in motos)
        lugares_same = all(l == lugares[0] for l in lugares)
        pilots_same = all(p == pilots[0] for p in pilots)

        primary = inputs[0]
        try:
            target_speed = float(primary.get('moto_data', {}).get('Velocidad Tope (km/h)') or 80)
        except (ValueError, TypeError):
            target_speed = 80.0

        accel_benchmarks = [v for v in range(0, int(target_speed) + 1, 20)]
        if accel_benchmarks[-1] < target_speed:
            accel_benchmarks.append(int(target_speed))

        parsed_data = []
        for i, inp in enumerate(inputs):
            df = parse_csv(inp['filepath'])
            if df.empty:
                continue
            df = convert_units(df)

            # Extraer Aceleración
            raw_accel = extract_acceleration_events(df, target_speed=target_speed)
            valid_accel = []
            seen_starts = set()
            for evt_df in raw_accel:
                s_idx = refine_acceleration_start(evt_df)
                if s_idx in seen_starts:
                    continue
                seen_starts.add(s_idx)

                ref_loc = evt_df.index.get_loc(s_idx)
                new_slice_start = max(0, ref_loc - 20)
                trimmed_df = evt_df.iloc[new_slice_start:].copy()
                trimmed_df.attrs = evt_df.attrs.copy()
                trimmed_df.attrs['start_idx'] = s_idx

                m = calculate_acceleration_metrics(trimmed_df, s_idx, target_speed=target_speed)
                if m:
                    # Validar continuidad de aceleración (sin caídas >= MAX_SPEED_DROP_KMH)
                    phase_v = trimmed_df.loc[s_idx:m['end_idx'], 'Velocidad_GPS']
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

                    v_s = trimmed_df.loc[s_idx, 'Velocidad_GPS']
                    if v_s < 5.0:
                        valid_accel.append({
                            'df': trimmed_df, 'metrics': m, 'pilot': inp['pilot'],
                            'weight': inp['weight'], 'id': len(valid_accel) + 1
                        })
            if valid_accel:
                valid_accel.sort(key=lambda x: x['metrics']['time_s'])

            # Extraer Recuperación
            raw_rec = extract_recovery_events(df, target_speed=target_speed)
            valid_rec = []
            for evt_df in raw_rec:
                m = calculate_recovery_metrics(evt_df)
                if m:
                    valid_rec.append({
                        'df': evt_df, 'metrics': m,
                        'group': evt_df.attrs.get('group'),
                        'pilot': inp['pilot'], 'weight': inp['weight'], 'id': len(valid_rec) + 1
                    })
            
            recovery_results = {}
            for g in [30, 40, 50]:
                group_evs = [e for e in valid_rec if e['group'] == g]
                if group_evs:
                    group_evs.sort(key=lambda x: x['metrics']['time_s'])
                    recovery_results[g] = {
                        'best': group_evs[0],
                        'top_3': group_evs[:3]
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
                'valid_accel': valid_accel,
                'recovery_results': recovery_results,
                'valid_rec': valid_rec,
                'pilot': inp['pilot'],
                'moto_data': motos[i],
                'lugar_data': lugares[i],
                'display_name': d_name,
                'id': i + 1
            })

        if not parsed_data:
            return False, "No se encontraron datos válidos en los archivos."

        # 2. Resumen Aceleración (mejor de cada archivo)
        best_accels_all = []
        for p in parsed_data:
            if p['valid_accel']:
                best_ev = p['valid_accel'][0].copy()
                best_ev['display_name'] = p['display_name']
                best_ev['id'] = p['id']
                best_accels_all.append(best_ev)

        # 3. Resumen Recuperación (mejores de cada banda por archivo)
        best_recs_all = []
        for p in parsed_data:
            for g in [30, 40, 50]:
                if g in p['recovery_results']:
                    best_ev = p['recovery_results'][g]['best'].copy()
                    best_ev['display_name'] = p['display_name']
                    best_ev['id'] = p['id']
                    best_recs_all.append(best_ev)

        # 4. Datos del Archivo 1 (como principal)
        primary = parsed_data[0]
        contexto_gps = get_gps_context(primary['df'])
        
        # Calcular distancia máxima entre todos los eventos de todos los archivos
        max_dist = 0.0
        for p in parsed_data:
            all_evs = p['valid_accel'] + p['valid_rec']
            for ev in all_evs:
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

        # Construir preview_data siguiendo estructura
        preview_data = {
            "type": "accel_recovery",
            "moto_info": primary['moto_data'], # Info general del arch 1
            "inputs": inputs,
            "comments": comments,
            "env_conditions": env_conditions,
            "contexto_gps": contexto_gps,
            "context_map": context_map,
            "accel_data": None,
            "recovery_data": None,
            "excel_cells": EXCEL_CELLS,
            "excel_img_sizes": EXCEL_IMG_SIZES,
        }

        sections = []

        # --- Secciones Aceleración ---
        if best_accels_all:
            img_combined = plot_speed_comparison(best_accels_all, f"Acceleration 0-{int(target_speed)} - General Result")
            
            sections.append({
                "title": f"Acceleration 0-{int(target_speed)} km/h - Summary",
                "images": [{'bytes': img_combined.getvalue()}],
                "table_data": None
            })

            # Detalle (solo arch 1)
            if primary['valid_accel']:
                best_accel_1 = primary['valid_accel'][0]
                img_detail_v = plot_speed_detailed(best_accel_1, "Speed vs Time", benchmarks=accel_benchmarks)
                img_detail_a = plot_accel_vs_time(best_accel_1, "Acceleration vs Time", benchmarks=accel_benchmarks)
                img_detail_rpm = plot_rpm_vs_time(best_accel_1, "RPM vs Time", benchmarks=accel_benchmarks) if 'RPM' in best_accel_1['df'].columns else None
                img_detail_gps = plot_gps_heatmap(best_accel_1, "Ubicación de la prueba")
                
                from utils.metrics_calculator import calculate_segments
                segments = calculate_segments(best_accel_1['df'], best_accel_1['metrics']['start_idx'], accel_benchmarks)
                bm = best_accel_1['metrics']
                segments.append([f"0-{int(target_speed)}", f"{bm['time_s']:.2f}", f"{bm['dist_m']:.2f}", f"{bm['avg_acc']:.2f}", f"{int(bm['top_rpm'])}"])

                imgs_detalle = []
                if img_detail_gps: imgs_detalle.append({'bytes': img_detail_gps.getvalue()})
                imgs_detalle.append({'bytes': img_detail_v.getvalue()})
                if img_detail_rpm: imgs_detalle.append({'bytes': img_detail_rpm.getvalue()})
                imgs_detalle.append({'bytes': img_detail_a.getvalue()})

                sections.append({
                    "title": f"Acceleration 0-{int(target_speed)} - Best Event ({primary['pilot']})",
                    "images": imgs_detalle,
                    "table_data": [["Segment (km/h)", "Time (s)", "Distance (m)", "Avg Acc (m/s²)", "Top RPM"]] + segments
                })

                preview_data["accel_data"] = {
                    "top_3_events": best_accels_all,
                    "segments": segments,
                    "img_combined": img_combined.getvalue(),
                    "img_detail_v": img_detail_v.getvalue(),
                    "img_detail_a": img_detail_a.getvalue(),
                    "img_detail_rpm": img_detail_rpm.getvalue() if img_detail_rpm else None,
                    "img_detail_gps": img_detail_gps.getvalue() if img_detail_gps else None,
                }
            else:
                preview_data["accel_data"] = {
                    "top_3_events": best_accels_all,
                    "img_combined": img_combined.getvalue(),
                    "segments": []
                }

        # -- Secciones Recuperación --
        if best_recs_all:
            img_combined_rec = plot_speed_comparison(best_recs_all, f"Acceleration 30-{int(target_speed)}, 40-{int(target_speed)}, 50-{int(target_speed)} - General Result")
            
            table_r = [["V. Start (km/h)", "V. End (km/h)", "Time (s)", "Distance (m)", "Avg Acc (m/s²)", "Top RPM"]]
            for ev in best_recs_all:
                m = ev['metrics']
                # Evitar prefijo duplicado en UI si es string custom
                table_r.append([f"{m['v_start']:.2f}", f"{m['v_final']:.2f}", f"{m['time_s']:.2f}",
                                f"{m['dist_m']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"])

            sections.append({
                "title": f"Recovery - General Summary (up to {int(target_speed)} km/h)",
                "images": [{'bytes': img_combined_rec.getvalue()}],
                "table_data": table_r
            })

            preview_data["recovery_data"] = {
                "summary_img": img_combined_rec.getvalue(),
                "summary_events": best_recs_all,
                "bands": {}
            }

            # Detalle recuperación (solo arch 1)
            if primary['recovery_results']:
                for g in [30, 40, 50]:
                    if g in primary['recovery_results']:
                        b = primary['recovery_results'][g]['best']
                        img_v = plot_speed_comparison([b], f"Speed vs Time ({g}-{int(target_speed)})")
                        img_a = plot_accel_vs_time(b, f"Acceleration vs Time ({g}-{int(target_speed)})")
                        img_rpm = plot_rpm_vs_time(b, f"RPM vs Time ({g}-{int(target_speed)})") if 'RPM' in primary['df'].columns else None
                        img_gps = plot_gps_heatmap(b, "Ubicación de la prueba")

                        m = b['metrics']
                        tab_b = [["V. Start", "V. End", "Time", "Distance", "Avg Acc", "Top RPM"],
                                 [f"{m['v_start']:.2f}", f"{m['v_final']:.2f}", f"{m['time_s']:.2f}",
                                  f"{m['dist_m']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"]]

                        imgs = []
                        if img_gps: imgs.append({'bytes': img_gps.getvalue()})
                        imgs.append({'bytes': img_v.getvalue()})
                        if img_rpm: imgs.append({'bytes': img_rpm.getvalue()})
                        imgs.append({'bytes': img_a.getvalue()})

                        sections.append({
                            "title": f"Recovery {g}-{int(target_speed)} km/h - Best Event",
                            "images": imgs,
                            "table_data": tab_b
                        })

                        preview_data["recovery_data"]["bands"][g] = {
                            "best_event": b,
                            "img_v": img_v.getvalue(),
                            "img_a": img_a.getvalue(),
                            "img_rpm": img_rpm.getvalue() if img_rpm else None,
                            "img_gps": img_gps.getvalue() if img_gps else None,
                        }

        from ui.preview_window import PreviewWindow

        def on_excel(p_data):
            from reports.excel_reporter import ExcelReporter
            try:
                r = ExcelReporter()
                ok, path = r.generate_accel_recovery(p_data)
                if ok:
                    messagebox.showinfo("Excel Guardado", f"Generado en:\n{path}")
                else:
                    messagebox.showerror("Excel Error", f"Error:\n{path}")
            except Exception as e:
                messagebox.showerror("Excel Exception", str(e))

        PreviewWindow(self, "Previsualización Comparativa - Aceleración y Recuperación",
                      sections, on_excel_callback=on_excel,
                      contexto_gps=contexto_gps, context_map=context_map,
                      preview_data=preview_data)
        
        return True, "Análisis comparativo procesado correctamente"
