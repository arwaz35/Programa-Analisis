"""
Detección y extracción de eventos desde los datos del datalogger.
Eventos se identifican por Pulsador == 100.
"""
import pandas as pd
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
