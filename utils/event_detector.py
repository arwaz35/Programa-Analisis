"""
Detección y extracción de eventos desde los datos del datalogger.
Eventos se identifican por Pulsador == 100.
"""
import pandas as pd
import numpy as np
from config import (TRIGGER_VALUE, TRIGGER_DEBOUNCE_SAMPLES,
                    SAMPLE_INTERVAL_S, RECOVERY_GROUPS)


def detect_trigger_groups(df):
    """
    Detecta grupos de triggers (Pulsador==100) con debounce.
    Retorna lista de índices de inicio de cada evento.
    """
    if 'Pulsador' not in df.columns:
        return []

    trigger_indices = df.index[df['Pulsador'] == TRIGGER_VALUE].tolist()

    grouped = []
    if trigger_indices:
        current_start = trigger_indices[0]
        prev_idx = trigger_indices[0]
        for idx in trigger_indices[1:]:
            if idx > prev_idx + TRIGGER_DEBOUNCE_SAMPLES:
                grouped.append(current_start)
                current_start = idx
            prev_idx = idx
        grouped.append(current_start)

    return grouped


def refine_acceleration_start(event_df):
    """
    Identifica el punto exacto donde la velocidad comienza a crecer desde ~0.
    Retorna el índice del inicio refinado.
    """
    try:
        starts = event_df.index[event_df['Velocidad_GPS'] < 1.0].tolist()
        if starts:
            return starts[-1]

        low_speed = event_df[event_df['Velocidad_GPS'] < 2.0]
        if not low_speed.empty:
            return low_speed.index[-1]

        return event_df.index[0]
    except Exception as e:
        print(f"Error refinando inicio de aceleración: {e}")
        return event_df.index[0]


def extract_acceleration_events(df, target_speed=80):
    """
    Extrae eventos de aceleración (0 → target_speed km/h).
    Criterios:
      1. Pulsador == 100
      2. Velocidad inicial ~ 0
      3. Alcanza target_speed
    Retorna lista de DataFrames, cada uno un evento.
    """
    events = []

    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events

    triggers = detect_trigger_groups(df)

    for start_idx in triggers:
        search_end = min(len(df), start_idx + 600)  # Max 60s

        post_trigger = df.iloc[start_idx:search_end]
        achieved = post_trigger[post_trigger['Velocidad_GPS'] >= target_speed]

        if achieved.empty:
            continue

        target_idx = achieved.index[0]
        target_loc = df.index.get_loc(target_idx)

        # Buffer: 2s antes del trigger, 1s después del target
        slice_start = max(0, start_idx - 20)
        slice_end = min(len(df), target_loc + 11)

        event_df = df.iloc[slice_start:slice_end].copy()

        if not event_df.empty:
            events.append(event_df)

    return events


def extract_recovery_events(df, target_speed=80):
    """
    Extrae eventos de recuperación (Vinicial → target_speed km/h).
    Agrupa por velocidad inicial: 30, 40, 50 km/h.
    Retorna lista de DataFrames con atributo 'group'.
    """
    events = []

    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events

    triggers = detect_trigger_groups(df)

    for start_idx in triggers:
        v_start = df.loc[start_idx, 'Velocidad_GPS']

        # Determinar grupo de velocidad
        group = None
        for g, (vmin, vmax) in RECOVERY_GROUPS.items():
            if vmin <= v_start < vmax:
                group = g
                break

        if group is None:
            continue  # No pertenece a ningún grupo de recuperación

        # Buscar target_speed
        search_end = min(len(df), start_idx + 600)
        post_trigger = df.iloc[start_idx:search_end]
        achieved = post_trigger[post_trigger['Velocidad_GPS'] >= target_speed]

        if achieved.empty:
            continue

        target_idx = achieved.index[0]
        target_loc = df.index.get_loc(target_idx)

        # Buffer
        slice_start = max(0, start_idx - 10)
        slice_end = min(len(df), target_loc + 11)

        event_df = df.iloc[slice_start:slice_end].copy()

        if not event_df.empty:
            event_df.attrs['group'] = group
            event_df.attrs['start_idx'] = start_idx
            event_df.attrs['end_idx'] = target_idx
            events.append(event_df)

    return events


def refine_braking_start(event_df, from_speed):
    """
    Identifica el punto exacto donde la frenada real comienza.
    Utiliza el método físico propuesto por Daniel: localiza el instante de máxima
    desaceleración (mínimo de Accel_X) y retrocede hasta el punto de mayor
    velocidad GPS en ese intervalo previo.
    Si no hay acelerómetro, realiza la misma lógica estimando la desaceleración
    por el cambio numérico de velocidad GPS.
    """
    try:
        speed = event_df['Velocidad_GPS'].values
        n_samples = len(speed)
        
        # 1. INTENTO CON ACELERÓMETRO LONGITUDINAL (Accel_X o Accel_X_ms2)
        accel_col = None
        if 'Accel_X_ms2' in event_df.columns:
            accel_col = 'Accel_X_ms2'
        elif 'Accel_X' in event_df.columns:
            accel_col = 'Accel_X'
            
        if accel_col:
            accel_series = event_df[accel_col].values
            
            # Suavizar señal del acelerómetro para evitar picos de ruido aislados (vibración del motor)
            accel_smooth = pd.Series(accel_series).rolling(window=5, min_periods=1, center=True).mean().values
            
            # Encontrar la desaceleración máxima (mínimo absoluto en la serie del acelerómetro)
            min_accel_idx = np.argmin(accel_smooth)
            
            # Buscar el punto de velocidad GPS máxima desde el inicio del evento
            # hasta el punto de desaceleración máxima
            if min_accel_idx > 0:
                sub_speed = speed[:min_accel_idx + 1]
                max_speed_local_idx = np.argmax(sub_speed)
                return event_df.index[max_speed_local_idx]
                
        # 2. FALLBACK SI NO HAY ACELERÓMETRO (ESTIMACIÓN POR GPS)
        # Calculamos la desaceleración numérica (derivada de la velocidad GPS suavizada)
        speed_smooth = pd.Series(speed).rolling(window=5, min_periods=1, center=True).mean().values
        calculated_decel = np.zeros(n_samples)
        window = 5
        for i in range(n_samples - window):
            v1_ms = speed_smooth[i] / 3.6
            v2_ms = speed_smooth[i + window] / 3.6
            dt = window * 0.1  # 10Hz
            calculated_decel[i] = (v1_ms - v2_ms) / dt
            
        max_decel_idx = np.argmax(calculated_decel)
        if max_decel_idx > 0:
            sub_speed = speed[:max_decel_idx + 1]
            max_speed_local_idx = np.argmax(sub_speed)
            return event_df.index[max_speed_local_idx]
            
        # Fallback de último recurso
        near_target = event_df[event_df['Velocidad_GPS'] >= from_speed * 0.9]
        if not near_target.empty:
            return near_target.index[0]
            
        return event_df.index[0]
    except Exception as e:
        print(f"Error refinando inicio de frenada (método de desaceleración): {e}")
        return event_df.index[0]


def extract_braking_events(df, from_speed=60):
    """
    Extrae eventos de frenado (from_speed → 0 km/h).
    Criterios:
      1. Pulsador == 100
      2. Velocidad cercana a from_speed en el trigger
      3. Velocidad desciende hasta < 1 km/h
    Retorna lista de DataFrames, cada uno un evento.
    """
    events = []

    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events

    triggers = detect_trigger_groups(df)

    for start_idx in triggers:
        v_at_trigger = df.loc[start_idx, 'Velocidad_GPS']

        # Verificar que la velocidad al momento del trigger está cerca del objetivo (rango +-10 km/h)
        if not (from_speed - 10 <= v_at_trigger <= from_speed + 10):
            continue

        # Buscar el punto donde la velocidad baja a < 1 km/h
        search_end = min(len(df), start_idx + 600)  # Max 60s
        post_trigger = df.iloc[start_idx:search_end]
        stopped = post_trigger[post_trigger['Velocidad_GPS'] < 1.0]

        if stopped.empty:
            continue

        end_idx = stopped.index[0]
        end_loc = df.index.get_loc(end_idx)

        # Buffer: 2s antes del trigger, 1s después del final
        slice_start = max(0, start_idx - 20)
        slice_end = min(len(df), end_loc + 11)

        event_df = df.iloc[slice_start:slice_end].copy()

        if not event_df.empty:
            events.append(event_df)

    return events


def extract_climbing_events(df, target_distance=70):
    """
    Extrae eventos de ascenso (0 km/h → target_distance metros).
    Criterios:
      1. Pulsador == 100
      2. Velocidad inicial ~ 0
      3. Recorre al menos target_distance metros
    Retorna lista de DataFrames.
    """
    events = []

    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events
    if 'Distancia' not in df.columns:
        return events

    triggers = detect_trigger_groups(df)

    for start_idx in triggers:
        v_start = df.loc[start_idx, 'Velocidad_GPS']
        if v_start > 5.0:  # Debe iniciar desde ~0
            continue

        d_start = df.loc[start_idx, 'Distancia']

        # Buscar dónde se alcanzan target_distance metros
        search_end = min(len(df), start_idx + 600)  # Max 60s
        post_trigger = df.iloc[start_idx:search_end]

        reached = post_trigger[(post_trigger['Distancia'] - d_start) >= target_distance]

        if reached.empty:
            continue

        end_idx = reached.index[0]
        end_loc = df.index.get_loc(end_idx)

        # Buffer
        slice_start = max(0, start_idx - 20)
        slice_end = min(len(df), end_loc + 11)

        event_df = df.iloc[slice_start:slice_end].copy()
        if not event_df.empty:
            event_df.attrs['start_idx'] = start_idx
            event_df.attrs['end_idx'] = end_idx
            events.append(event_df)

    return events


def extract_topspeed_events(df, min_distance=200):
    """
    Extrae eventos de velocidad máxima.
    Criterios:
      1. Pulsador == 100
      2. Velocidad alta al momento del trigger
      3. Se mantiene durante al menos min_distance metros
    Retorna lista de DataFrames.
    """
    events = []

    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events
    if 'Distancia' not in df.columns:
        return events

    triggers = detect_trigger_groups(df)

    for start_idx in triggers:
        v_at_trigger = df.loc[start_idx, 'Velocidad_GPS']

        # Debe estar a velocidad alta (al menos 30 km/h)
        if v_at_trigger < 30:
            continue

        d_start = df.loc[start_idx, 'Distancia']

        # Buscar dónde se recorren min_distance metros
        search_end = min(len(df), start_idx + 600)  # Max 60s
        post_trigger = df.iloc[start_idx:search_end]

        reached = post_trigger[(post_trigger['Distancia'] - d_start) >= min_distance]

        if reached.empty:
            continue

        end_idx = reached.index[0]
        end_loc = df.index.get_loc(end_idx)

        # Buffer
        slice_start = max(0, start_idx - 20)
        slice_end = min(len(df), end_loc + 11)

        event_df = df.iloc[slice_start:slice_end].copy()
        if not event_df.empty:
            event_df.attrs['start_idx'] = start_idx
            event_df.attrs['end_idx'] = end_idx
            events.append(event_df)

    return events


def export_event_to_csv(event, output_dir, moto_info, lugar_name, test_name="Prueba"):
    """
    Exporta un evento individual a CSV.
    Formato: (Prueba)_(Motocicleta)_(Codigo)_(Lugar)_(Fecha).csv
    """
    import os

    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        def clean(s):
            return "".join([c for c in str(s) if c.isalnum() or c in (' ', '-', '_')]).strip()

        moto_str = clean(moto_info.get('Nombre Comercial', 'Moto'))
        modelo_str = clean(moto_info.get('Código Modelo', 'Modelo'))
        lugar_str = clean(lugar_name)
        test_str = clean(test_name)
        fecha_str = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

        filename = f"{test_str}_{moto_str}_{modelo_str}_{lugar_str}_{fecha_str}.csv"
        filepath = os.path.join(output_dir, filename)

        df_export = event['df'].copy()
        df_export.to_csv(filepath, index=False)
        return filepath
    except Exception as e:
        print(f"Error exportando CSV: {e}")
        return None
