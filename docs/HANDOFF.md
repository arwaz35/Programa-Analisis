# HANDOFF — Registro de Cambios del Programa Análisis

> Este documento registra todos los cambios significativos realizados en el proyecto.
> Cada entrada nueva se agrega al inicio de la sección **Registro de Cambios**.

---

## Información General

| Campo                       | Valor                             |
| --------------------------- | --------------------------------- |
| **Proyecto**          | Programa Análisis — INCOL       |
| **Ruta**              | `Programa Analisis/`            |
| **Versión actual**   | 1.0.5                             |
| **Programa anterior** | `Programa Resultados/` (v2.9.1) |
| **Lenguaje**          | Python 3                          |
| **Framework UI**      | CustomTkinter                     |

---

## Registro de Cambios

### v1.0.5 — Filtro de Intentos Abortados en Aceleración y Recuperación (2026-06-17)

**Objetivo:** Evitar que un intento de prueba fallido o abortado (donde el vehículo se detiene antes de alcanzar la velocidad objetivo) ensucie o altere el eje de tiempo de las aceleraciones y recuperaciones válidas subsiguientes.

* **Detector de Parada en Aceleración (`event_detector.py`)**:
  * En `extract_acceleration_events`, se introdujo un algoritmo de histéresis: si la velocidad supera **$5.0$ km/h** (inicio de movimiento) y posteriormente vuelve a caer por debajo de **$2.0$ km/h** (moto detenida), se considera que el intento de aceleración se abortó.
  * La ventana de búsqueda del trigger se trunca en la detención, evitando enlazar un trigger abortado con un intento exitoso posterior. Esto elimina desfases y jorobas de tiempo (por ejemplo, previas de hasta 22 segundos en el eje X) en gráficas de motos limitadas a 60 km/h.
*   **Detector de Parada en Recuperación (`event_detector.py`)**:
    *   En `extract_recovery_events`, si la velocidad disminuye por debajo de **$10.0$ km/h** antes de alcanzar la velocidad objetivo, se asume que la prueba de recuperación fue abortada y se trunca la búsqueda.
*   **Actualización de Plantillas Excel (`excel_reporter.py`)**:
    *   Se actualizaron los nombres de archivo hardcoded de las plantillas en `excel_reporter.py` para coincidir con las nuevas versiones almacenadas en la carpeta `Formatos/`:
        *   Aceleración: `ft-nm-000-008.xlsx` → `FT-NM-000-008V1.xlsx`
        *   Frenado: `ft-nm-000-005.xlsx` → `FT-NM-000-005V3.xlsx`
        *   Ascenso: `ft-nm-000-012.xlsx` → `FT-NM-000-012V4.xlsx`
        *   Velocidad Máxima: `ft-nm-000-007.xlsx` → `FT-NM-000-007V4.xlsx`

---

### v1.0.4 — Refinamiento Físico de Inicio de Frenado v3 (2026-06-06)

**Objetivo:** Eliminar los tramos planos de velocidad constante en las previsualizaciones de frenado y sincronizar el punto de inicio de la prueba de forma precisa con el pico anterior a la caída de velocidad continua.

* **Detección de Desaceleración Activa (`event_detector.py`)**:
  * Se optimizó el algoritmo en `refine_braking_start` para identificar el primer punto donde la desaceleración del acelerómetro (suavizada con media móvil) cruza por debajo de los **$-0.3$ G** (frenado activo real).
  * Se configuró el inicio de la prueba ($t = 0$) en la **muestra inmediatamente anterior** a dicho cruce. Esto alinea la gráfica perfectamente en el pico máximo de velocidad (por ejemplo, fila `5386` de Excel en el Evento 5), logrando que la curva de velocidad descienda inmediatamente sin tramos planos.
  * Se integró la misma lógica en el fallback de velocidad GPS, detectando cuándo la desaceleración calculada supera $1.0$ m/s² y retrocediendo una muestra.

---

### v1.0.3 — Refinamiento Híbrido de Inicio de Frenado (2026-06-06)

**Objetivo:** Introducir la detección física de inicio de frenado basada en los sensores del datalogger.

* **Algoritmo de Refinamiento Híbrido (`event_detector.py`)**:
  * Implementación de detección basada en el acelerómetro longitudinal (`Accel_X` o `Accel_X_ms2`) suavizado con una media móvil para mitigar el ruido por vibración del motor de la moto.
  * Localización de la desaceleración máxima en la ventana del evento y retroceso al pico de velocidad máximo local.

---

### v1.0.2 — Refinamiento de Inicio de Frenado por Caída de Velocidad (2026-06-06)

**Objetivo:** Refinar el punto exacto donde se inicia la deceleración real mediante algoritmos de tendencia.

* **Filtro de Descenso Sostenido (`event_detector.py`)**:
  * Se implementó una lógica de análisis en `refine_braking_start` basada en la caída sostenida de velocidad de al menos $4.0$ km/h en $1.0$ segundo y posterior búsqueda de máximo local.

---

### v1.0.1 — Control de Rangos de Velocidad de Frenado (2026-06-06)

**Objetivo:** Agrupar y filtrar estrictamente los eventos de frenado dentro de los límites solicitados de $40 \pm 5$ km/h y $60 \pm 5$ km/h.

* **Filtro en el Trigger (`event_detector.py`)**:
  * Se modificó `extract_braking_events` para validar que la velocidad en el trigger (`v_at_trigger`) esté en el rango de `from_speed +- 10` km/h. Esto evita que eventos de 60 km/h se extraigan como si fueran de 40 km/h.
* **Filtro Estricto en Velocidad Inicial (`braking.py`)**:
  * Se modificaron `_process_single` y `_process_comparison` para aplicar un filtro estricto de `from_speed +- 5` km/h a la velocidad inicial real (`v_start`) calculada a partir del inicio refinado. Los eventos que queden fuera se descartan de los análisis y gráficos.

---

### v1.0.0 — Módulos Finales y Estandarización (2026-05-12)

**Objetivo:** Finalización de los 3 módulos core faltantes (Frenado, Ascenso, Velocidad Máxima) y estandarización de reportes Excel con unidades físicas.

#### 1. Nuevos Módulos de Análisis

Se han implementado y estabilizado los siguientes módulos:

* **Módulo de Frenado (`braking.py`)**:
  * Análisis de frenado 40→0 y 60→0 km/h.
  * Detección inteligente de inicio de frenada (ventana de 1.5s para filtrar fluctuaciones).
  * Soporte para comparación de hasta 3 archivos.
* **Módulo de Ascenso (`climbing.py`)**:
  * Análisis de desempeño en pendiente (~12°).
  * Interfaz especial: Lugar general + Fila 1 (Solo Piloto) + Fila 2 (Con Pasajero).
  * Cálculo automático de pendiente (%, °) basado en altitud GPS.
* **Módulo de Velocidad Máxima (`top_speed.py`)**:
  * Mantenimiento de velocidad en tramos de 200m.
  * Comparativa de Velocidad GPS vs. Velocidad de Tablero.
  * Cálculo de diferencia porcentual de error del velocímetro.

#### 2. Mejoras en Core y Utilidades

* **Detección de Eventos (`event_detector.py`)**:
  * `refine_braking_start`: Implementación de lógica de validación (13/15 muestras decrecientes) para asegurar que la métrica de tiempo/distancia de frenado sea exacta.
* **Calculadora de Métricas (`metrics_calculator.py`)**:
  * Nuevas funciones para cálculo de pendiente, desaceleración negativa y diferencias de velocidad.
* **Visualización de Mapas (`map_plotter.py`)**:
  * Soporte para superposición de datos de pendiente (`slope_data`) en los mapas de contexto.

#### 3. Estandarización de Reportes Excel

* **Unidades Físicas**: Se ha implementado la adición automática de unidades en todos los formatos:
  * Peso: `XX kg`
  * Altura: `XXX cm`
* **Nuevas Plantillas**: Integración total con los formatos:
  * `ft-nm-000-005.xlsx` (Frenado)
  * `ft-nm-000-012.xlsx` (Ascenso)
  * `ft-nm-000-007.xlsx` (Velocidad Máxima)

---

### v0.0.1 — Creación inicial (2026-05-01)

**Objetivo:** Refactorizar `Programa Resultados` en una arquitectura modular limpia, eliminando PDF y ranking, manteniendo solo Excel como salida.

#### Estructura creada

```
Programa Analisis/
├── main.py                          # Punto de entrada, menú principal
├── config.py                        # Rutas, constantes, detección de OS
├── version.py                       # Control de versión
├── data_handler.py                  # CRUD motos, pilotos, lugares (JSON)
├── requirements.txt                 # Dependencias
├── data/
│   ├── motos.json                   # BD de motocicletas
│   ├── pilotos.json                 # BD de pilotos
│   └── lugares.json                 # BD de lugares
├── docs/
│   └── HANDOFF.md                   # Este archivo
├── utils/
│   ├── csv_parser.py                # Lectura CSV con detección de separador
│   ├── event_detector.py            # Detección de eventos (pulsador, aceleración, recuperación)
│   ├── metrics_calculator.py        # Cálculo de métricas (tiempo, distancia, aceleración)
│   └── gps_utils.py                 # Contexto GPS, coordenadas, Google Maps
├── plotting/
│   ├── base_plotter.py              # Config global matplotlib, helpers
│   ├── speed_plotter.py             # Velocidad vs tiempo
│   ├── accel_plotter.py             # Aceleración vs tiempo
│   ├── rpm_plotter.py               # RPM vs tiempo
│   └── map_plotter.py               # Mapas GPS con mapa de calor
├── modules/
│   ├── base_module.py               # Clase abstracta base para todos los módulos
│   ├── acceleration.py              # ✅ Módulo completo (Aceleración + Recuperación)
│   ├── braking.py                   # ⏳ Esqueleto — no implementado
│   ├── climbing.py                  # ⏳ Esqueleto — no implementado
│   └── top_speed.py                 # ⏳ Esqueleto — no implementado
├── reports/
│   └── excel_reporter.py            # Generador de reportes Excel
└── ui/
    ├── preview_window.py            # Ventana de previsualización
    └── management/
        ├── motos_view.py            # Gestión de motos
        ├── pilotos_view.py          # Gestión de pilotos
        └── lugares_view.py          # Gestión de lugares
```

#### Cambios principales vs `Programa Resultados`

| Aspecto            | Antes (v2.9.1)                             | Ahora (v0.0.1)                                                  |
| ------------------ | ------------------------------------------ | --------------------------------------------------------------- |
| Salida de reportes | PDF + Excel                                | **Solo Excel**                                            |
| Ranking            | Sí (`ranking.json`)                     | **Eliminado**                                             |
| Estructura         | Código mezclado en pocos archivos grandes | **24 archivos** en 6 paquetes                             |
| Imágenes Excel    | `AbsoluteAnchor` (posición fija en EMU) | Ancla por celda (`ws.add_image(img, 'B59')`)                  |
| Interfaz           | Menú con 3 modos (Comp/Todas/Indiv.)      | **2 pantallas**: Menú → Selección de Pruebas           |
| Mapeo de celdas    | Hardcoded en `excel_reporter.py`         | **Diccionario `EXCEL_CELLS`** al inicio de cada módulo |
| Rutas              | Hardcoded para Mac                         | **Detección automática** de OS (Windows/Mac)            |
| Datos              | JSON en carpeta raíz                      | JSON en `data/` dedicada                                      |

#### Módulo de Aceleración — Detalles

- Fusiona aceleración (0→80 km/h) y recuperación (30/40/50→80 km/h)
- Soporta 1 o 2 archivos CSV (comparación pendiente de completar)
- Genera: gráficas comparativas, gráficas detalladas, mapas GPS con mapa de calor
- Previsualización scrollable antes de exportar
- Mapeo de celdas Excel configurable en `EXCEL_CELLS` (formato `ft-nm-000-008.xlsx`)

#### Dependencias

```
pandas, numpy, matplotlib, customtkinter, staticmap, Pillow, openpyxl
```

#### Preguntas resueltas (2026-05-01)

1. ✅ **Fotos de piloto** → Se almacenan en `../Pilotos/` con el nombre del piloto. Se seleccionan desde la gestión de pilotos. Para aceleración, celdas de pasajero quedan vacías.
2. ✅ **"Origen"** → Campo nuevo agregado a la gestión de motos y BD.
3. ✅ **Pasajero en aceleración** → No aplica. Celdas J30-J34 quedan vacías.
4. ✅ **Mapeo de celdas** → Se usa exclusivamente el mapeo nuevo (líneas 545-654 de `Nuevas funciones.txt`).

#### Verificación

- ✅ Programa ejecuta sin errores (`python main.py`)
- ✅ Interfaz abre correctamente
- ⏳ Pendiente: prueba funcional con datos CSV reales

---

### Ajustes post-creación (2026-05-01)

**Archivos modificados:**

- `config.py` → Agregada ruta `PILOTOS_FOTOS_DIR` apuntando a `../Pilotos/`
- `ui/management/motos_view.py` → Agregada columna y campo "Origen" en tabla y formulario de creación
- `ui/management/pilotos_view.py` → Rediseñada con:
  - Layout de 2 columnas: tabla (izquierda) + panel de foto (derecha)
  - Columna "Foto" en tabla con indicador ✅/❌
  - Previsualización de foto al seleccionar un piloto
  - Botón "📷 Asignar Foto" para asignar/cambiar foto desde el explorador de archivos
  - La foto se copia a `../Pilotos/{NombrePiloto}.ext`
  - Al renombrar un piloto, la foto se renombra automáticamente

---

### Fotos de motos + inserción en Excel (2026-05-01)

**Archivos modificados:**

- `config.py` → Agregada ruta `MOTOS_FOTOS_DIR` apuntando a `../Motos/`
- `ui/management/motos_view.py` → Rediseñada con:
  - Layout de 2 columnas: tabla (izquierda) + panel de foto (derecha)
  - Columna "Foto" en tabla con indicador ✅/❌
  - Previsualización de foto al seleccionar una moto
  - Botón "📷 Asignar Foto" para asignar/cambiar foto
  - La foto se copia a `../Motos/{NombreComercial Placa}.ext`
  - Función `get_moto_foto_path()` exportada para uso en el excel_reporter
- `reports/excel_reporter.py` → Inserción automática de:
  - Foto de moto → celda `Y7` (si disponible)
  - Foto de piloto → celda `B34` (si disponible)
  - Nuevo método `_insert_image_from_file()` para insertar imágenes desde disco

---

### v0.0.3 — Bugfix foto persistente (2026-05-01)

**Bug corregido:** Al seleccionar un piloto/moto con foto y luego seleccionar uno sin foto, la imagen anterior permanecía visible. Se corrigió limpiando la referencia `_ctk_image = None` en los bloques `else` y `except` de `_show_photo()`.

**Archivos modificados:**

- `ui/management/motos_view.py` → Limpieza de `_ctk_image` cuando no hay foto
- `version.py` → 0.0.3

---

### v0.0.4 — Estabilización y Git (2026-05-01)

**Mejoras técnicas:**

- **Git independiente:** Se inicializó un repositorio Git exclusivo para `Programa Analisis` para no mezclarlo con versiones anteriores.
- **Dependencias:** Se instaló `openpyxl` para habilitar la generación de reportes Excel.
- **Fix Crítico (TclError):** Se corrigió el error `image "pyimageX" doesn't exist` al cambiar fotos. Ahora el label de imagen se destruye y recrea en cada selección para asegurar que CustomTkinter no pierda las referencias internas.
- **Fix Importación:** Se movieron `get_moto_foto_path` y `get_piloto_foto_path` a nivel de módulo en sus respectivas vistas para permitir que `excel_reporter.py` las importe y use al generar el informe.

**Archivos modificados:**

- `ui/management/pilotos_view.py` & `motos_view.py` → Rediseño de lógica de visualización de fotos.
- `reports/excel_reporter.py` → Corrección de imports y lógica de inserción de fotos.
- `version.py` → 0.0.4

---

### v0.0.5 — Edición de motos y lugares (2026-05-01)

**Funcionalidad nueva:** Se agregó la capacidad de modificar registros existentes de motocicletas y lugares, igualando la funcionalidad que ya existía en la gestión de pilotos.

- Botón **"Actualizar Datos"** (amarillo) aparece en motos y lugares al seleccionar un registro.
- El formulario de actualización se abre prellenado con los datos actuales.
- En motos, si se cambia el nombre/placa, la foto se renombra automáticamente.

**Archivos modificados:**

- `data_handler.py` → Nuevo método `update_lugar(index, lugar_data)`
- `ui/management/motos_view.py` → Función `update_moto()` + botón `btn_upd`
- `ui/management/lugares_view.py` → Función `update_lugar()` + botón `btn_upd`, refactorización de `select_row` para guardar datos del lugar seleccionado
- `version.py` → 0.0.5

### v0.0.9 — Internacionalización y Mejoras Visuales (2026-05-03)

**Objetivo:** Traducir el sistema al inglés para estandarización técnica y mejorar la precisión visual de las gráficas y reportes Excel.

#### Mejoras de Internacionalización y Visualización

- **Gráficas en Inglés:** Todos los títulos, etiquetas de ejes (`Speed (km/h)`, `Time (s)`, `Acceleration (m/s²)`) y leyendas se tradujeron al inglés.
- **Mapas Limpios:** Se eliminaron los títulos internos de los mapas GPS para ganar espacio visual.
- **Anotaciones Técnicas:** "Promedio Global" se cambió por `Acc Avg`.
- **Leyendas Inteligentes:** En la gráfica de velocidad detallada, la leyenda se movió a la esquina superior derecha (`upper right`) para evitar que se cruce con la línea de datos.

#### Mejoras en Reporte Excel (ft-nm-000-008.xlsx)

- **Tabla de Recuperación Extendida:** Ahora muestra los **9 mejores eventos** (los 3 mejores de 30-80, los 3 mejores de 40-80 y los 3 mejores de 50-80).
- **Nomenclatura de Eventos:** Se simplificó el nombre (`Evento {id} (30-80)` → `Event {id}`).
- **Nueva Tabla de Segmentos (0-80):** Se reestructuró la sección del mejor evento de aceleración. Ahora las filas 101 a 105 contienen los segmentos (0-20, 20-40, 40-60, 60-80 y 0-80) con columnas:
  - **B**: Segment Name
  - **E**: Time
  - **H**: Distance
  - **K**: Avg Acc
  - **N**: Top RPM
- **Mapa de Calor:** Reubicado de la celda `B103` a la `B107` para dar espacio a la nueva tabla de segmentos.

#### Lógica de Análisis

- **Distancia de Pista (T35):** Ahora se calcula buscando el evento con el **recorrido más largo** dentro del archivo CSV, en lugar de usar la distancia total del archivo, proporcionando una escala más precisa para el mapa de trazado.

**Archivos modificados:**

- `plotting/speed_plotter.py`, `accel_plotter.py`, `rpm_plotter.py`, `map_plotter.py`
- `modules/acceleration.py`
- `reports/excel_reporter.py`
- `main.py`, `version.py`

---
