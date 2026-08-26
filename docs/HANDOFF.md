# HANDOFF — Registro de Cambios del Programa Análisis

> Este documento registra todos los cambios significativos realizados en el proyecto.
> Cada entrada nueva se agrega al inicio de la sección **Registro de Cambios**.

---

## Información General

| Campo                       | Valor                             |
| --------------------------- | --------------------------------- |
| **Proyecto**          | Programa Análisis — INCOL       |
| **Ruta**              | `Programa Analisis/`            |
| **Versión actual**   | 1.1.0                             |
| **Programa anterior** | `Programa Resultados/` (v2.9.1) |
| **Lenguaje**          | Python 3                          |
| **Framework UI**      | CustomTkinter                     |

---

## Registro de Cambios

### v1.1.0 — Separación de Modos (Individual / Comparación) y Detección Inteligente (2026-08-24)

**Objetivo:** Reestructurar la interfaz de usuario en dos modos de trabajo independientes (**Individual** y **Comparación**) con diseño compartido de dos columnas, simplificando la captura de datos en pruebas individuales a 1 solo archivo y dotando al sistema de detección inteligente de variables de comparación sin alterar el formato estándar de Excel.

* **Menú Principal con Flujos Independientes (`main.py`)**:
  * Se sustituyó el botón genérico por dos accesos principales: **"🔬 Individual"** y **"⚖️ Comparación"**.
  * Ambas vistas comparten el layout simétrico: Columna izquierda con selector de pruebas, condiciones ambientales, comentarios y botón de previsualización; Columna derecha con los controles dinámicos de archivo según el módulo.
* **Simplificación de Pruebas Individuales (`modules/acceleration.py`, `braking.py`, `top_speed.py`)**:
  * En modo **Individual**, los módulos de Aceleración, Frenado y Velocidad Máxima presentan únicamente **1 fila de archivo CSV**, optimizando el flujo para la evaluación a fondo de una sola moto.
  * El módulo de **Ascenso** (`climbing.py`) mantiene sus 2 filas fijas (*Solo Piloto* y *Con Pasajero*).
* **Módulo de Comparación Multi-Archivo (`modules/`)**:
  * En modo **Comparación**, los módulos habilitan hasta 3 archivos para comparar pasadas superpuestas en las gráficas de previsualización.
  * **Enfoque Exclusivo en Comparación:** Se eliminaron las gráficas de detalle individual sesgadas al Archivo 1, presentando únicamente las curvas comparativas superpuestas (`img_combined`) y las tablas de resultados consolidados de todas las motos/archivos analizados.
  * En Ascenso, se presenta una pantalla informativa de *"Módulo en construcción / Próximamente"*.
* **Detección Inteligente de Nombres y Leyendas**:
  * El sistema identifica automáticamente qué variable cambia entre los archivos analizados para rotular las leyendas de las gráficas y la columna *C (Evento)* de las tablas resumen:
    1. Si cambian las motocicletas $\rightarrow$ Se rotula con el **Código de Modelo** (`Código Modelo` / `Codigo`).
    2. Si las motos son iguales pero cambian los pilotos $\rightarrow$ Se rotula con el **Nombre del Piloto**.
    3. Si motos y pilotos son iguales pero cambian los lugares $\rightarrow$ Se rotula con el **Nombre del Lugar**.
    4. Si todo es idéntico $\rightarrow$ Se rotula como `Pasada 1`, `Pasada 2`, etc.
* **Integridad Total del Formato Excel (`excel_reporter.py`)**:
  * Las plantillas y coordenadas de celdas no sufren ninguna alteración, garantizando compatibilidad 100% con los formatos oficiales estándar.

---

### v1.0.10 — Inserción de Foto de Pasajero en Reportes Excel (2026-08-19)

**Objetivo:** Corregir la ausencia de la foto del pasajero en el informe Excel generado para pruebas de ascenso (y demás módulos donde se configure pasajero).

* **Inserción de Foto de Pasajero (`excel_reporter.py`)**:
  * En `_fill_common_data` y `generate_climbing`, se agregó la llamada a `_insert_image_from_file` para buscar y colocar la foto del pasajero (`get_piloto_foto_path(pax_name)`) en la celda `pasajero_foto` (`J48` en ascenso, `J50` en aceleración).
  * Se agregó soporte para leer el pasajero de cualquiera de las entradas configuradas (`inputs[1]` o `inputs[0]`).

---

### v1.0.9 — Robustez y Fiabilidad en la Generación de Mapas GPS (2026-08-19)

**Objetivo:** Eliminar la intermitencia en la generación de mapas GPS (como el mapa de trazado del lugar o el mapa de recuperación 40-80 en los reportes Excel) causada por timeouts de red al verificar conexión o descargar cuadrículas de satélite.

* **Caché y Verificación Multi-Servidor (`map_plotter.py`)**:
  * Se implementó un sistema de caché de conexión a internet (`cache_ttl=60` s) para evitar comprobaciones de red redundantes y lentas antes de cada sub-mapa.
  * Se agregaron múltiples servidores DNS de contingencia (`8.8.8.8`, `1.1.1.1`, `8.8.4.4`) con timeout extendido ($2.5\text{ s}$) para prevenir falsos negativos por latencia o jitter de red.
* **Reintentos Automáticos de Descarga de Cuadrículas (`map_plotter.py`)**:
  * Tanto `plot_gps_heatmap` como `plot_gps_route_simple` ahora reintentan hasta 3 veces automáticamente ante fallas transitorias en la descarga de teselas/cuadrículas satelitales.
* **Fallback para Mapa de Contexto (`acceleration.py`)**:
  * Se añadió un fallback seguro para el trazado de la pista cuando no existan eventos 0-80 (usando eventos de recuperación o el recorrido global).

---

### v1.0.8 — Filtro de Descarte por Desaceleración Anómala / Frenada en Pruebas (2026-08-18)

**Objetivo:** Descartar automáticamente pasadas de aceleración y ascenso que presenten interrupciones, frenadas o pérdidas severas de tracción antes de alcanzar la distancia o velocidad objetivo, evitando que curvas de velocidad anómalas (como caídas de velocidad a mitad de la subida) se clasifiquen como válidas.

* **Constante Global `MAX_SPEED_DROP_KMH` (`config.py`)**:
  * Se configuró en **$7.0\text{ km/h}$** la caída máxima permitida de velocidad respecto al pico alcanzado durante la marcha activa ($v \ge 8.0\text{ km/h}$).
* **Detección y Truncamiento por Caída de Velocidad (`event_detector.py`)**:
  * En `extract_climbing_events` y `extract_acceleration_events`, si la velocidad disminuye $\ge 7.0\text{ km/h}$ respecto a la velocidad máxima acumulada durante el intento, la búsqueda se trunca y el intento se descarta por falta de continuidad.
* **Validación Doble de Continuidad (`climbing.py`, `acceleration.py`)**:
  * Se agregó una verificación estricta en el tramo útil de aceleración para garantizar que ninguna pasada con caídas $\ge 7.0\text{ km/h}$ ingrese al ranking de mejores eventos o al informe Excel.

---

### v1.0.7 — Delimitación Inteligente de Triggers y Normalización de Buffer Previo (2026-08-18)

**Objetivo:** Evitar que pulsaciones accidentales o repetidas en plena marcha ($v > 5.0\text{ km/h}$) interrumpan o descarten pruebas válidas en curso, y eliminar tiempos muertos prolongados en las gráficas cuando el piloto demora varios segundos en arrancar tras accionar el pulsador.

* **Delimitación Inteligente entre Triggers (`event_detector.py`)**:
  * En `extract_climbing_events` y `extract_acceleration_events`, se actualizó la regla de corte entre triggers:
    * Un trigger posterior solo delimita/anula al trigger anterior si ocurre mientras la motocicleta aún permanece detenida ($v \le 5.0\text{ km/h}$ en todo el tramo intermedio) o después de haberse detenido tras completar/abortar el intento previo.
    * Las pulsaciones que ocurran mientras la moto ya va en plena marcha ($v > 5.0\text{ km/h}$) se ignoran y no interrumpen la prueba en curso, rescatando pasadas completas que antes eran canceladas indebidamente (ej. Pasada 2 en `Ray Z ascenso pasajero.csv`).
* **Normalización de Buffer Previo (`climbing.py`, `acceleration.py`)**:
  * El DataFrame del evento se recorta automáticamente para comenzar exactamente **20 muestras ($\approx 2.0\text{ s}$)** antes del despegue real (`s_idx_refined`), eliminando cualquier línea horizontal kilométrica a $0\text{ km/h}$ en las gráficas si el piloto esperó en reposo antes de arrancar.
* **Deduplicación de Eventos Físicos (`climbing.py`, `acceleration.py`)**:
  * Se implementó un filtro de unicidad basado en `s_idx_refined` para asegurar que múltiples pulsaciones asociadas al mismo arranque computen una sola vez.

---

### v1.0.6 — Corrección de Detección de Eventos y Refinamiento Contextual de Inicio en Ascenso y Demás Pruebas (2026-08-14)

**Objetivo:** Corregir la detección errónea de eventos en pruebas de ascenso donde maniobras previas o intentos abortados eran fusionados indebidamente con pasadas posteriores, generando tiempos distorsionados (como $8.8\text{ s}$ en lugar de $10.1\text{ s}$ por medir distancias incompletas) y colas negativas extensas en el eje de tiempo de las gráficas (ej. $-26.4\text{ s}$).

* **Detección de Paradas en Ascenso (`event_detector.py`)**:
  * En `extract_climbing_events`, se introdujo detección de paradas por histéresis: si la motocicleta inicia movimiento ($v > 5.0\text{ km/h}$) pero se detiene ($v < 2.0\text{ km/h}$) antes de recorrer los 70 metros, la búsqueda se trunca y el intento abortado o maniobra se descarta automáticamente.
* **Delimitación Estricta entre Triggers (`event_detector.py`)**:
  * Se restringió la ventana máxima de búsqueda en `extract_climbing_events`, `extract_acceleration_events`, `extract_recovery_events`, `extract_braking_events` y `extract_topspeed_events` para que ningún evento busque más allá del siguiente trigger consecutivo (`triggers[i+1]`).
* **Refinamiento de Inicio Contextual (`event_detector.py`)**:
  * En `refine_acceleration_start`, se eliminó la búsqueda global `starts[-1]` (que saltaba a paradas intermedias decenas de segundos en el futuro).
  * Ahora analiza el entorno local del trigger: identifica el despegue de la rampa de velocidad ($v \ge 2.0\text{ km/h}$) y toma la última muestra previa en reposo ($v < 1.0\text{ km/h}$) o busca hacia atrás en el buffer previo si el trigger se pulsó en movimiento.
* **Estandarización de Atributos (`event_detector.py`)**:
  * Todos los extractores ahora registran consistentemente `event_df.attrs['start_idx']` y `event_df.attrs['end_idx']`.

---

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
