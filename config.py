"""
Configuración global del programa.
Rutas, constantes y detección de sistema operativo.
"""
import os
import platform

# ══════════════════════════════════════════════════
# DETECCIÓN DE SISTEMA OPERATIVO
# ══════════════════════════════════════════════════
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

# ══════════════════════════════════════════════════
# RUTAS DEL PROYECTO
# ══════════════════════════════════════════════════
# Ruta base del programa (donde está este archivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta raíz del proyecto Datalogger (un nivel arriba)
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Carpeta de formatos Excel
FORMATOS_DIR = os.path.join(PROJECT_DIR, "Formatos")

# Carpeta de resultados
RESULTADOS_DIR = os.path.join(PROJECT_DIR, "Resultados")

# Carpeta de datos internos (motos, pilotos, lugares)
DATA_DIR = os.path.join(BASE_DIR, "data")

# Carpeta de fotos de pilotos
PILOTOS_FOTOS_DIR = os.path.join(PROJECT_DIR, "Pilotos")

# Carpeta de fotos de motos
MOTOS_FOTOS_DIR = os.path.join(PROJECT_DIR, "Motos")

# ══════════════════════════════════════════════════
# CONSTANTES FÍSICAS Y DE MUESTREO
# ══════════════════════════════════════════════════
G_TO_MS2 = 9.80665          # Conversión de G a m/s²
SAMPLE_RATE_HZ = 10         # Frecuencia de muestreo del datalogger
SAMPLE_INTERVAL_S = 0.1     # Intervalo entre muestras (1/SAMPLE_RATE_HZ)

# ══════════════════════════════════════════════════
# CONSTANTES DE ANÁLISIS
# ══════════════════════════════════════════════════
TRIGGER_VALUE = 100          # Valor del pulsador que inicia un evento
TRIGGER_DEBOUNCE_SAMPLES = 10  # Muestras mínimas entre triggers distintos (1 segundo)

# Agrupación de velocidades para recuperación
RECOVERY_GROUPS = {
    30: (25, 35),   # Velocidad 30 km/h: rango 25-35
    40: (35, 45),   # Velocidad 40 km/h: rango 35-45
    50: (45, 55),   # Velocidad 50 km/h: rango 45-55
}

# Benchmarks de velocidad para análisis detallado de aceleración
ACCEL_BENCHMARKS = [0, 20, 40, 60, 80]

# ══════════════════════════════════════════════════
# TAMAÑOS DE GRÁFICAS (para Excel, en cm)
# ══════════════════════════════════════════════════
IMG_SIZE_MAP = (15.5, 10.5)           # Ancho x Alto - Mapas
IMG_SIZE_SUMMARY = (17.5, 11.5)      # Ancho x Alto - Gráfica mejores eventos
IMG_SIZE_DETAIL_VEL = (17.5, 7.0)    # Ancho x Alto - Velocidad vs tiempo (mejor evento)
IMG_SIZE_DETAIL_SMALL = (17.5, 4.0)  # Ancho x Alto - Aceleración/RPM (mejor evento)

# ══════════════════════════════════════════════════
# INICIALIZACIÓN DE CARPETAS
# ══════════════════════════════════════════════════
def ensure_directories():
    """Crea las carpetas necesarias si no existen."""
    for d in [RESULTADOS_DIR, DATA_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)
