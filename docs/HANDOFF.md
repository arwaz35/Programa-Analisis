# HANDOFF — Registro de Cambios del Programa Análisis

> Este documento registra todos los cambios significativos realizados en el proyecto.
> Cada entrada nueva se agrega al inicio de la sección **Registro de Cambios**.

---

## Información General

| Campo | Valor |
|---|---|
| **Proyecto** | Programa Análisis — INCOL |
| **Ruta** | `Programa Analisis/` |
| **Versión actual** | 0.0.1 |
| **Programa anterior** | `Programa Resultados/` (v2.9.1) |
| **Lenguaje** | Python 3 |
| **Framework UI** | CustomTkinter |

---

## Registro de Cambios

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

| Aspecto | Antes (v2.9.1) | Ahora (v0.0.1) |
|---|---|---|
| Salida de reportes | PDF + Excel | **Solo Excel** |
| Ranking | Sí (`ranking.json`) | **Eliminado** |
| Estructura | Código mezclado en pocos archivos grandes | **24 archivos** en 6 paquetes |
| Imágenes Excel | `AbsoluteAnchor` (posición fija en EMU) | Ancla por celda (`ws.add_image(img, 'B59')`) |
| Interfaz | Menú con 3 modos (Comp/Todas/Indiv.) | **2 pantallas**: Menú → Selección de Pruebas |
| Mapeo de celdas | Hardcoded en `excel_reporter.py` | **Diccionario `EXCEL_CELLS`** al inicio de cada módulo |
| Rutas | Hardcoded para Mac | **Detección automática** de OS (Windows/Mac) |
| Datos | JSON en carpeta raíz | JSON en `data/` dedicada |

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

