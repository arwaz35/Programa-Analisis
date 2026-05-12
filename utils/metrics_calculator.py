"""
Cálculo de métricas de rendimiento para los eventos extraídos.
"""
import math
import pandas as pd
from config import SAMPLE_INTERVAL_S


def calculate_acceleration_metrics(event_df, start_idx, target_speed=80):
    """
    Calcula métricas para un evento de aceleración 0→target.
    Retorna dict con: time_s, dist_m, avg_acc, v_final, top_rpm, start_idx, end_idx
    """
    try:
        start_loc = event_df.index.get_loc(start_idx)
        sub_df = event_df.iloc[start_loc:]

        targets = sub_df.index[sub_df['Velocidad_GPS'] >= target_speed].tolist()
        if not targets:
            return None

        end_idx = targets[0]
        phase = event_df.loc[start_idx:end_idx]

        time_s = (len(phase) - 1) * SAMPLE_INTERVAL_S

        # Distancia
        if 'Distancia' in phase.columns:
            d_start = phase.loc[start_idx, 'Distancia']
            d_end = phase.loc[end_idx, 'Distancia']
            dist_m = d_end - d_start
            if dist_m < 0:
                dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()

        # Aceleración promedio
        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()
        else:
            v_final_ms = phase.loc[end_idx, 'Velocidad_GPS'] / 3.6
            v_start_ms = phase.loc[start_idx, 'Velocidad_GPS'] / 3.6
            avg_acc = (v_final_ms - v_start_ms) / time_s if time_s > 0 else 0

        return {
            'time_s': time_s,
            'dist_m': dist_m,
            'avg_acc': avg_acc,
            'v_start': phase.loc[start_idx, 'Velocidad_GPS'],
            'v_final': phase.loc[end_idx, 'Velocidad_GPS'],
            'top_rpm': phase['RPM'].max() if 'RPM' in phase.columns else 0,
            'start_idx': start_idx,
            'end_idx': end_idx
        }
    except Exception as e:
        print(f"Error calculando métricas de aceleración: {e}")
        return None


def calculate_recovery_metrics(event_df):
    """
    Calcula métricas para un evento de recuperación.
    Usa start_idx y end_idx almacenados en attrs del DataFrame.
    """
    try:
        start_idx = event_df.attrs.get('start_idx')
        end_idx = event_df.attrs.get('end_idx')

        if start_idx is None or end_idx is None:
            return None
        if start_idx not in event_df.index or end_idx not in event_df.index:
            return None

        phase = event_df.loc[start_idx:end_idx]
        time_s = (len(phase) - 1) * SAMPLE_INTERVAL_S

        if 'Distancia' in phase.columns:
            dist_m = phase.loc[end_idx, 'Distancia'] - phase.loc[start_idx, 'Distancia']
            if dist_m < 0:
                dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()

        avg_acc = 0
        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()

        return {
            'time_s': time_s,
            'dist_m': dist_m,
            'avg_acc': avg_acc,
            'v_start': phase.loc[start_idx, 'Velocidad_GPS'],
            'v_final': phase.loc[end_idx, 'Velocidad_GPS'],
            'top_rpm': phase['RPM'].max() if 'RPM' in phase.columns else 0,
            'start_idx': start_idx,
            'end_idx': end_idx
        }
    except Exception as e:
        print(f"Error calculando métricas de recuperación: {e}")
        return None


def calculate_segments(event_df, start_idx, benchmarks):
    """
    Calcula métricas por segmentos de velocidad.
    Ej: benchmarks=[0,20,40,60,80] → segmentos 0-20, 20-40, 40-60, 60-80
    Retorna lista de listas: [segmento, tiempo, distancia, aceleración, rpm]
    """
    segments = []

    try:
        start_loc = event_df.index.get_loc(start_idx)
        sub = event_df.iloc[start_loc:]

        for i in range(len(benchmarks) - 1):
            v1 = benchmarks[i]
            v2 = benchmarks[i + 1]

            # Buscar inicio del segmento
            if v1 == 0:
                s_idx = sub.index[0]
            else:
                c1 = sub[sub['Velocidad_GPS'] >= v1]
                if c1.empty:
                    continue
                s_idx = c1.index[0]

            # Buscar fin del segmento
            sub2 = sub.loc[s_idx:]
            c2 = sub2[sub2['Velocidad_GPS'] >= v2]
            if c2.empty:
                continue
            e_idx = c2.index[0]

            seg_slice = event_df.loc[s_idx:e_idx]
            t_seg = (event_df.index.get_loc(e_idx) - event_df.index.get_loc(s_idx)) * SAMPLE_INTERVAL_S

            # Distancia del segmento
            if 'Distancia' in event_df.columns:
                d_seg = max(0, event_df.loc[e_idx, 'Distancia'] - event_df.loc[s_idx, 'Distancia'])
            else:
                d_seg = 0

            a_seg = seg_slice['Accel_X_ms2'].mean() if 'Accel_X_ms2' in seg_slice.columns else 0
            rpm_seg = seg_slice['RPM'].max() if 'RPM' in seg_slice.columns else 0

            segments.append([
                f"{v1}-{v2}",
                f"{t_seg:.2f}",
                f"{d_seg:.2f}",
                f"{a_seg:.2f}",
                f"{int(rpm_seg)}"
            ])

    except Exception as e:
        print(f"Error calculando segmentos: {e}")

    return segments


def calculate_braking_metrics(event_df, start_idx, end_idx):
    """
    Calcula métricas para un evento de frenado (from_speed → 0).
    La desaceleración se reporta como valor negativo.
    Retorna dict con: time_s, dist_m, avg_acc, v_start, v_final, top_rpm, start_idx, end_idx
    """
    try:
        if start_idx not in event_df.index or end_idx not in event_df.index:
            return None

        phase = event_df.loc[start_idx:end_idx]
        time_s = (len(phase) - 1) * SAMPLE_INTERVAL_S

        # Distancia
        if 'Distancia' in phase.columns:
            d_start = phase.loc[start_idx, 'Distancia']
            d_end = phase.loc[end_idx, 'Distancia']
            dist_m = d_end - d_start
            if dist_m < 0:
                dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()

        # Desaceleración promedio (negativa)
        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()
        else:
            v_start_ms = phase.loc[start_idx, 'Velocidad_GPS'] / 3.6
            v_end_ms = phase.loc[end_idx, 'Velocidad_GPS'] / 3.6
            avg_acc = (v_end_ms - v_start_ms) / time_s if time_s > 0 else 0

        return {
            'time_s': time_s,
            'dist_m': dist_m,
            'avg_acc': avg_acc,
            'v_start': phase.loc[start_idx, 'Velocidad_GPS'],
            'v_final': phase.loc[end_idx, 'Velocidad_GPS'],
            'top_rpm': phase['RPM'].max() if 'RPM' in phase.columns else 0,
            'start_idx': start_idx,
            'end_idx': end_idx
        }
    except Exception as e:
        print(f"Error calculando métricas de frenado: {e}")
        return None


def calculate_climbing_metrics(event_df, start_idx, end_idx):
    """
    Calcula métricas para un evento de ascenso.
    Retorna dict con: time_s, dist_m, avg_acc, v_start, v_final, top_rpm, start_idx, end_idx
    """
    try:
        if start_idx not in event_df.index or end_idx not in event_df.index:
            return None

        phase = event_df.loc[start_idx:end_idx]
        time_s = (len(phase) - 1) * SAMPLE_INTERVAL_S

        if 'Distancia' in phase.columns:
            dist_m = phase.loc[end_idx, 'Distancia'] - phase.loc[start_idx, 'Distancia']
            if dist_m < 0:
                dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()

        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()
        else:
            v_final_ms = phase.loc[end_idx, 'Velocidad_GPS'] / 3.6
            v_start_ms = phase.loc[start_idx, 'Velocidad_GPS'] / 3.6
            avg_acc = (v_final_ms - v_start_ms) / time_s if time_s > 0 else 0

        return {
            'time_s': time_s,
            'dist_m': dist_m,
            'avg_acc': avg_acc,
            'v_start': phase.loc[start_idx, 'Velocidad_GPS'],
            'v_final': phase.loc[end_idx, 'Velocidad_GPS'],
            'top_rpm': phase['RPM'].max() if 'RPM' in phase.columns else 0,
            'start_idx': start_idx,
            'end_idx': end_idx
        }
    except Exception as e:
        print(f"Error calculando métricas de ascenso: {e}")
        return None


def calculate_topspeed_metrics(event_df, start_idx, end_idx):
    """
    Calcula métricas para un evento de velocidad máxima.
    Retorna dict con: max_speed, avg_acc, top_rpm, time_s, dist_m, start_idx, end_idx
    """
    try:
        if start_idx not in event_df.index or end_idx not in event_df.index:
            return None

        phase = event_df.loc[start_idx:end_idx]
        time_s = (len(phase) - 1) * SAMPLE_INTERVAL_S
        max_speed = phase['Velocidad_GPS'].max()

        if 'Distancia' in phase.columns:
            dist_m = phase.loc[end_idx, 'Distancia'] - phase.loc[start_idx, 'Distancia']
            if dist_m < 0:
                dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * SAMPLE_INTERVAL_S).sum()

        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()
        else:
            avg_acc = 0

        return {
            'max_speed': max_speed,
            'time_s': time_s,
            'dist_m': dist_m,
            'avg_acc': avg_acc,
            'v_start': phase.loc[start_idx, 'Velocidad_GPS'],
            'v_final': phase.loc[end_idx, 'Velocidad_GPS'],
            'top_rpm': phase['RPM'].max() if 'RPM' in phase.columns else 0,
            'start_idx': start_idx,
            'end_idx': end_idx
        }
    except Exception as e:
        print(f"Error calculando métricas de velocidad máxima: {e}")
        return None


def calculate_slope(event_df, start_idx, end_idx):
    """
    Calcula la pendiente/inclinación del terreno usando datos GPS.
    Retorna dict con: slope_pct, angle_deg, delta_alt, delta_dist
    """
    try:
        if 'Altitud' not in event_df.columns or 'Distancia' not in event_df.columns:
            return None

        phase = event_df.loc[start_idx:end_idx]

        alt_start = phase['Altitud'].iloc[0]
        alt_end = phase['Altitud'].iloc[-1]
        delta_alt = alt_end - alt_start

        dist_start = phase['Distancia'].iloc[0]
        dist_end = phase['Distancia'].iloc[-1]
        delta_dist = dist_end - dist_start

        if delta_dist <= 0:
            return None

        slope_pct = (delta_alt / delta_dist) * 100
        angle_deg = math.degrees(math.atan(delta_alt / delta_dist))

        return {
            'slope_pct': round(slope_pct, 2),
            'angle_deg': round(angle_deg, 2),
            'delta_alt': round(delta_alt, 2),
            'delta_dist': round(delta_dist, 2)
        }
    except Exception as e:
        print(f"Error calculando pendiente: {e}")
        return None


def calculate_speed_difference(gps_speed, dashboard_speed):
    """
    Calcula la diferencia porcentual entre la velocidad del tablero y la del GPS.
    GPS es la velocidad real de referencia.
    Retorna el porcentaje de diferencia.
    """
    try:
        gps = float(gps_speed)
        dash = float(dashboard_speed)
        if gps <= 0:
            return None
        return round(((dash - gps) / gps) * 100, 2)
    except (ValueError, TypeError):
        return None
