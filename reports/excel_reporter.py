"""
Generador de reportes Excel.
Usa plantillas .xlsx y las llena con datos e imágenes.
"""
import os
import io
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
import pandas as pd
from PIL import Image
from config import FORMATOS_DIR, RESULTADOS_DIR, PILOTOS_FOTOS_DIR, MOTOS_FOTOS_DIR


class ExcelReporter:
    def __init__(self, templates_dir=None, output_dir=None):
        self.templates_dir = templates_dir or FORMATOS_DIR
        self.output_dir = output_dir or RESULTADOS_DIR

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _insert_image(self, ws, img_bytes, cell, width_cm=None, height_cm=None):
        """
        Inserta una imagen en una celda específica del worksheet.
        Si se proporcionan width_cm y height_cm, redimensiona la imagen.
        """
        if not img_bytes:
            return

        if isinstance(img_bytes, dict):
            img_bytes = img_bytes.get('bytes')
        if not img_bytes:
            return

        try:
            pil_img = Image.open(io.BytesIO(img_bytes))
            img_buf = io.BytesIO()
            pil_img.save(img_buf, format='PNG')
            img_buf.seek(0)

            xl_img = OpenpyxlImage(img_buf)

            # Redimensionar si se especifica
            if width_cm and height_cm:
                xl_img.width = width_cm / 2.54 * 72   # cm → puntos (72 puntos por pulgada)
                xl_img.height = height_cm / 2.54 * 72
            elif width_cm:
                # Mantener relación de aspecto
                orig_w, orig_h = pil_img.size
                ratio = orig_h / orig_w
                xl_img.width = width_cm / 2.54 * 72
                xl_img.height = xl_img.width * ratio

            ws.add_image(xl_img, cell)
        except Exception as e:
            print(f"Error insertando imagen en {cell}: {e}")

    def _insert_image_from_file(self, ws, filepath, cell, width_cm=None, height_cm=None):
        """
        Inserta una imagen desde un archivo en disco en una celda del worksheet.
        Se usa para fotos de moto y piloto.
        """
        if not filepath or not os.path.exists(filepath):
            return

        try:
            pil_img = Image.open(filepath)
            img_buf = io.BytesIO()
            pil_img.save(img_buf, format='PNG')
            img_buf.seek(0)

            xl_img = OpenpyxlImage(img_buf)

            if width_cm and height_cm:
                xl_img.width = width_cm / 2.54 * 72
                xl_img.height = height_cm / 2.54 * 72
            elif width_cm:
                orig_w, orig_h = pil_img.size
                ratio = orig_h / orig_w
                xl_img.width = width_cm / 2.54 * 72
                xl_img.height = xl_img.width * ratio

            ws.add_image(xl_img, cell)
        except Exception as e:
            print(f"Error insertando imagen de archivo {filepath} en {cell}: {e}")

    @staticmethod
    def _fmt(val, dec=2):
        """Formatea un valor numérico."""
        if val is None or val == "":
            return ""
        try:
            return round(float(val), dec)
        except (ValueError, TypeError):
            return str(val)

    def generate_accel_recovery(self, preview_data):
        """
        Genera el reporte Excel de aceleración y recuperación
        usando el formato ft-nm-000-008.xlsx.
        """
        try:
            template_path = os.path.join(self.templates_dir, "ft-nm-000-008.xlsx")
            if not os.path.exists(template_path):
                return False, f"Plantilla no encontrada: {template_path}"

            wb = openpyxl.load_workbook(template_path)
            ws = wb.active

            # Leer mapeo de celdas del módulo
            cells = preview_data.get('excel_cells', {})
            sizes = preview_data.get('excel_img_sizes', {})

            moto = preview_data.get('moto_info', {})
            env_cond = preview_data.get('env_conditions', {})
            lugar = env_cond.get('lugar', {}) if env_cond else {}
            inputs = preview_data.get('inputs', [{}])[0]
            ctx = preview_data.get('contexto_gps', {})

            # ── INFORMACIÓN GENERAL ──
            ws[cells.get("modelo_codigo", "B9")] = f"{moto.get('Nombre Comercial', '')} ({moto.get('Código Modelo', '')})"
            ws[cells.get("fecha", "N7")] = pd.Timestamp.now().strftime("%d/%m/%Y")
            ws[cells.get("placa", "N9")] = moto.get('Placa', '')
            ws[cells.get("chasis", "N10")] = moto.get('Chasis', '')
            ws[cells.get("motor", "N11")] = moto.get('Motor', '')
            ws[cells.get("origen", "N8")] = moto.get('Origen', '')
            ws[cells.get("comentarios", "A24")] = preview_data.get('comments', '')

            # ── FOTO DE MOTO ──
            from ui.management.motos_view import get_moto_foto_path
            moto_foto = get_moto_foto_path(moto)
            if moto_foto:
                self._insert_image_from_file(ws, moto_foto,
                                            cells.get("foto_moto", "Y7"),
                                            width_cm=5.0)

            # ── CONDICIONES ──
            ws[cells.get("piloto_nombre", "B30")] = inputs.get('pilot', '')
            ws[cells.get("piloto_peso", "B31")] = self._fmt(inputs.get('weight', ''), 0)
            ws[cells.get("piloto_altura", "B32")] = self._fmt(inputs.get('altura', ''), 0)

            # ── FOTO DE PILOTO ──
            from ui.management.pilotos_view import get_piloto_foto_path
            piloto_foto = get_piloto_foto_path(inputs.get('pilot', ''))
            if piloto_foto:
                self._insert_image_from_file(ws, piloto_foto,
                                            cells.get("piloto_foto", "B34"),
                                            width_cm=5.0)

            ws[cells.get("lugar_nombre", "W30")] = lugar.get('Nombre', '')
            if ctx:
                ws[cells.get("lugar_altitud", "W31")] = self._fmt(ctx.get('altitud_promedio_msnm', ''))
                ws[cells.get("lugar_coordenadas", "W32")] = f"{ctx.get('latitud_inicial', '')}, {ctx.get('longitud_inicial', '')}"
                ws[cells.get("lugar_link", "W33")] = ctx.get('google_maps_link', '')
            else:
                ws[cells.get("lugar_altitud", "W31")] = lugar.get('Altitud (msnm)', '')

            ws[cells.get("temp_ambiente", "AG30")] = self._fmt(env_cond.get('temp_amb', '')) if env_cond else ''
            ws[cells.get("humedad", "AG31")] = self._fmt(env_cond.get('humidity', '')) if env_cond else ''
            ws[cells.get("temp_suelo", "AG32")] = self._fmt(env_cond.get('temp_ground', '')) if env_cond else ''

            # ── MAPA CONTEXTO ──
            map_size = sizes.get("mapa", (10.5, 15.5))
            self._insert_image(ws, preview_data.get('context_map'),
                              cells.get("mapa_trazado", "T35"),
                              width_cm=map_size[1], height_cm=map_size[0])

            # ── ACELERACIÓN 0-80 ──
            a_data = preview_data.get('accel_data')
            if a_data:
                start_row = cells.get("accel_start_row", 59)
                for i, ev in enumerate(a_data.get('top_3_events', [])):
                    row = start_row + i
                    m = ev['metrics']
                    ws[f"{cells.get('accel_col_num', 'B')}{row}"] = i + 1
                    ws[f"{cells.get('accel_col_evento', 'C')}{row}"] = f"Event {ev['id']}"
                    ws[f"{cells.get('accel_col_vi', 'E')}{row}"] = self._fmt(m.get('v_start', 0))
                    ws[f"{cells.get('accel_col_vf', 'G')}{row}"] = self._fmt(m.get('v_final', 0))
                    ws[f"{cells.get('accel_col_tiempo', 'I')}{row}"] = self._fmt(m.get('time_s', 0))
                    ws[f"{cells.get('accel_col_dist', 'K')}{row}"] = self._fmt(m.get('dist_m', 0))
                    ws[f"{cells.get('accel_col_acel', 'M')}{row}"] = self._fmt(m.get('avg_acc', 0))
                    ws[f"{cells.get('accel_col_rpm', 'O')}{row}"] = self._fmt(m.get('top_rpm', 0), 0)

                # Gráfica resumen
                res_size = sizes.get("grafica_resumen", (11.5, 17.5))
                self._insert_image(ws, a_data.get('img_combined'),
                                  cells.get("accel_img_resumen", "R55"),
                                  width_cm=res_size[1], height_cm=res_size[0])

                # Best event - Tabla de segmentos (filas 101-105)
                seg_start = cells.get("seg_start_row", 101)
                segments = a_data.get('segments', [])
                for i, seg in enumerate(segments):
                    row = seg_start + i
                    # seg = [segment_name, time, distance, acc, rpm]
                    ws[f"{cells.get('seg_col_name', 'B')}{row}"] = seg[0]
                    ws[f"{cells.get('seg_col_time', 'E')}{row}"] = self._fmt(seg[1])
                    ws[f"{cells.get('seg_col_dist', 'H')}{row}"] = self._fmt(seg[2])
                    ws[f"{cells.get('seg_col_acc', 'K')}{row}"] = self._fmt(seg[3])
                    ws[f"{cells.get('seg_col_rpm', 'N')}{row}"] = self._fmt(seg[4], 0)

                # Imágenes del mejor evento
                vel_size = sizes.get("grafica_vel", (7.0, 17.5))
                small_size = sizes.get("grafica_small", (4.0, 17.5))

                self._insert_image(ws, a_data.get('img_detail_gps'),
                                  cells.get("best_accel_img_mapa", "B103"),
                                  width_cm=map_size[1], height_cm=map_size[0])
                self._insert_image(ws, a_data.get('img_detail_v'),
                                  cells.get("best_accel_img_vel", "R97"),
                                  width_cm=vel_size[1], height_cm=vel_size[0])
                self._insert_image(ws, a_data.get('img_detail_a'),
                                  cells.get("best_accel_img_acel", "R109"),
                                  width_cm=small_size[1], height_cm=small_size[0])
                self._insert_image(ws, a_data.get('img_detail_rpm'),
                                  cells.get("best_accel_img_rpm", "R115"),
                                  width_cm=small_size[1], height_cm=small_size[0])

            # ── RECUPERACIÓN ──
            r_data = preview_data.get('recovery_data')
            if r_data:
                # Tabla resumen
                rec_start = cells.get("rec_start_row", 79)
                for i, ev in enumerate(r_data.get('summary_events', [])):
                    row = rec_start + i
                    m = ev['metrics']
                    ws[f"{cells.get('rec_col_num', 'B')}{row}"] = i + 1
                    ws[f"{cells.get('rec_col_evento', 'C')}{row}"] = f"Event {ev['id']}"
                    ws[f"{cells.get('rec_col_vi', 'E')}{row}"] = self._fmt(m.get('v_start', 0))
                    ws[f"{cells.get('rec_col_vf', 'G')}{row}"] = self._fmt(m.get('v_final', 0))
                    ws[f"{cells.get('rec_col_tiempo', 'I')}{row}"] = self._fmt(m.get('time_s', 0))
                    ws[f"{cells.get('rec_col_dist', 'K')}{row}"] = self._fmt(m.get('dist_m', 0))
                    ws[f"{cells.get('rec_col_acel', 'M')}{row}"] = self._fmt(m.get('avg_acc', 0))
                    ws[f"{cells.get('rec_col_rpm', 'O')}{row}"] = self._fmt(m.get('top_rpm', 0), 0)

                res_size = sizes.get("grafica_resumen", (11.5, 17.5))
                self._insert_image(ws, r_data.get('summary_img'),
                                  cells.get("rec_img_resumen", "R75"),
                                  width_cm=res_size[1], height_cm=res_size[0])

                # Bandas individuales
                bands_config = {
                    30: {"row_key": "best_rec30_row", "vel_key": "best_rec30_img_vel",
                         "acel_key": "best_rec30_img_acel", "rpm_key": "best_rec30_img_rpm",
                         "mapa_key": "best_rec30_img_mapa"},
                    40: {"row_key": "best_rec40_row", "vel_key": "best_rec40_img_vel",
                         "acel_key": "best_rec40_img_acel", "rpm_key": "best_rec40_img_rpm",
                         "mapa_key": "best_rec40_img_mapa"},
                    50: {"row_key": "best_rec50_row", "vel_key": "best_rec50_img_vel",
                         "acel_key": "best_rec50_img_acel", "rpm_key": "best_rec50_img_rpm",
                         "mapa_key": "best_rec50_img_mapa"},
                }

                bands = r_data.get('bands', {})
                vel_size = sizes.get("grafica_vel", (7.0, 17.5))
                small_size = sizes.get("grafica_small", (4.0, 17.5))

                for spd, conf in bands_config.items():
                    b_info = bands.get(spd)
                    if not b_info:
                        continue

                    m = b_info['best_event']['metrics']
                    rw = cells.get(conf["row_key"], 126)

                    ws[f"{cells.get('rec_col_num', 'B')}{rw}"] = 1
                    ws[f"{cells.get('rec_col_evento', 'C')}{rw}"] = f"Best {spd}-80"
                    ws[f"{cells.get('rec_col_vi', 'E')}{rw}"] = self._fmt(m.get('v_start', 0))
                    ws[f"{cells.get('rec_col_vf', 'G')}{rw}"] = self._fmt(m.get('v_final', 0))
                    ws[f"{cells.get('rec_col_tiempo', 'I')}{rw}"] = self._fmt(m.get('time_s', 0))
                    ws[f"{cells.get('rec_col_dist', 'K')}{rw}"] = self._fmt(m.get('dist_m', 0))
                    ws[f"{cells.get('rec_col_acel', 'M')}{rw}"] = self._fmt(m.get('avg_acc', 0))
                    ws[f"{cells.get('rec_col_rpm', 'O')}{rw}"] = self._fmt(m.get('top_rpm', 0), 0)

                    self._insert_image(ws, b_info.get('img_gps'),
                                      cells.get(conf["mapa_key"], "B128"),
                                      width_cm=map_size[1], height_cm=map_size[0])
                    self._insert_image(ws, b_info.get('img_v'),
                                      cells.get(conf["vel_key"], "R122"),
                                      width_cm=vel_size[1], height_cm=vel_size[0])
                    self._insert_image(ws, b_info.get('img_a'),
                                      cells.get(conf["acel_key"], "R134"),
                                      width_cm=small_size[1], height_cm=small_size[0])
                    self._insert_image(ws, b_info.get('img_rpm'),
                                      cells.get(conf["rpm_key"], "R140"),
                                      width_cm=small_size[1], height_cm=small_size[0])

            # ── GUARDAR ──
            def clean(s):
                return "".join([c for c in str(s) if c.isalnum() or c in (' ', '-', '_')]).strip()

            moto_str = clean(moto.get('Nombre Comercial', 'Moto'))
            fecha_str = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Aceleracion_y_Recuperacion_{moto_str}_{fecha_str}.xlsx"
            filepath = os.path.join(self.output_dir, filename)

            wb.save(filepath)
            return True, filepath

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, str(e)
