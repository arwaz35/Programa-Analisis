"""
Utilidades GPS: contexto geográfico, coordenadas, links de Google Maps.
"""
import numpy as np


def clean_coordinate(val):
    """Convierte un valor de coordenada (string o float) a float."""
    if isinstance(val, str):
        try:
            return float(val.replace(',', '.'))
        except ValueError:
            return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def get_gps_context(df):
    """
    Extrae contexto GPS del DataFrame: coordenadas, altitud, distancia, link.
    Retorna dict con la información geográfica.
    """
    context = {}

    try:
        if 'Latitud' not in df.columns or 'Longitud' not in df.columns:
            return context

        lats = df['Latitud'].apply(clean_coordinate).dropna()
        lons = df['Longitud'].apply(clean_coordinate).dropna()

        # Filtrar coordenadas inválidas (0,0)
        valid_mask = (lats != 0) & (lons != 0)
        lats = lats[valid_mask]
        lons = lons[valid_mask]

        if lats.empty or lons.empty:
            return context

        context['latitud_inicial'] = round(lats.iloc[0], 6)
        context['longitud_inicial'] = round(lons.iloc[0], 6)
        context['latitud_final'] = round(lats.iloc[-1], 6)
        context['longitud_final'] = round(lons.iloc[-1], 6)
        context['latitud_centro'] = round(lats.mean(), 6)
        context['longitud_centro'] = round(lons.mean(), 6)

        # Altitud
        if 'Altitud' in df.columns:
            alts = df['Altitud'].apply(clean_coordinate).dropna()
            alts = alts[alts != 0]
            if not alts.empty:
                context['altitud_promedio_msnm'] = round(alts.mean(), 1)

        # Distancia total
        if 'Distancia' in df.columns:
            dist_vals = df['Distancia'].dropna()
            if not dist_vals.empty:
                context['distancia_m'] = round(dist_vals.max() - dist_vals.min(), 2)

        # Link de Google Maps
        lat_c = context.get('latitud_centro', context.get('latitud_inicial'))
        lon_c = context.get('longitud_centro', context.get('longitud_inicial'))
        if lat_c and lon_c:
            context['google_maps_link'] = f"https://www.google.com/maps?q={lat_c},{lon_c}"

    except Exception as e:
        print(f"Error obteniendo contexto GPS: {e}")

    return context


def prepare_gps_data(df, start_idx=None, end_idx=None):
    """
    Prepara datos GPS limpios para graficar (lat, lon, velocidad).
    Retorna (lats, lons, velocities) como arrays de numpy o None si no hay datos válidos.
    """
    try:
        if start_idx is not None and end_idx is not None:
            try:
                s_loc = df.index.get_loc(start_idx)
                e_loc = df.index.get_loc(end_idx)
                run_df = df.iloc[s_loc:e_loc + 1].copy()
            except Exception:
                run_df = df.copy()
        else:
            run_df = df.copy()

        if run_df.empty:
            return None

        if 'Latitud' not in run_df.columns or 'Longitud' not in run_df.columns:
            return None

        run_df['Lat'] = run_df['Latitud'].apply(clean_coordinate)
        run_df['Lon'] = run_df['Longitud'].apply(clean_coordinate)

        valid_df = run_df.dropna(subset=['Lat', 'Lon'])
        valid_df = valid_df[(valid_df['Lat'] != 0) & (valid_df['Lon'] != 0)]

        if len(valid_df) < 2:
            return None

        lats = valid_df['Lat'].values
        lons = valid_df['Lon'].values
        velocities = valid_df['Velocidad_GPS'].values if 'Velocidad_GPS' in valid_df.columns else np.zeros(len(valid_df))

        return lats, lons, velocities
    except Exception as e:
        print(f"Error preparando datos GPS: {e}")
        return None
