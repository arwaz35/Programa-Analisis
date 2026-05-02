"""
Lectura y conversión de archivos CSV del datalogger.
"""
import pandas as pd
from config import G_TO_MS2


def parse_csv(filepath):
    """
    Lee un archivo CSV detectando automáticamente el separador (, o ;).
    Retorna un DataFrame de pandas.
    """
    try:
        df = pd.read_csv(filepath, sep=',')
        if len(df.columns) < 2:
            df = pd.read_csv(filepath, sep=';')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error leyendo CSV {filepath}: {e}")
        return pd.DataFrame()


def convert_units(df):
    """
    Convierte columnas de aceleración de G a m/s².
    """
    if 'Accel_X' in df.columns:
        df['Accel_X_ms2'] = df['Accel_X'] * G_TO_MS2
    if 'Accel_Y' in df.columns:
        df['Accel_Y_ms2'] = df['Accel_Y'] * G_TO_MS2
    return df
