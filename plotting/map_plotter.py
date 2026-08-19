"""
Gráficas de mapas GPS con mapa de calor de velocidad.
"""
from plotting.base_plotter import save_to_buffer
from utils.gps_utils import prepare_gps_data
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import io
import socket
import time

_INTERNET_CACHE = {'connected': None, 'timestamp': 0}


def _check_internet(cache_ttl=60):
    """
    Verifica conexión a internet de forma confiable con caché.
    Consulta múltiples servidores DNS con un timeout de 2.5 segundos.
    """
    now = time.time()
    if _INTERNET_CACHE['connected'] is not None and (now - _INTERNET_CACHE['timestamp']) < cache_ttl:
        return _INTERNET_CACHE['connected']

    hosts = [('8.8.8.8', 53), ('1.1.1.1', 53), ('8.8.4.4', 53)]
    for host, port in hosts:
        try:
            socket.create_connection((host, port), timeout=2.5)
            _INTERNET_CACHE['connected'] = True
            _INTERNET_CACHE['timestamp'] = now
            return True
        except OSError:
            continue

    _INTERNET_CACHE['connected'] = False
    _INTERNET_CACHE['timestamp'] = now
    return False


def plot_gps_heatmap(event, title="Ubicación de la prueba"):
    """
    Genera mapa GPS con línea de calor por velocidad.
    Azul=lento, Rojo=rápido.
    Retorna BytesIO con la imagen PNG.
    """
    try:
        if not _check_internet():
            print("Sin conexión a internet, saltando mapa GPS.")
            return None

        from staticmap import StaticMap, Line

        df = event['df']
        start_idx = event['metrics'].get('start_idx')
        end_idx = event['metrics'].get('end_idx')

        gps_data = prepare_gps_data(df, start_idx, end_idx)
        if gps_data is None:
            return None

        lats, lons, velocities = gps_data

        # Crear mapa
        url_template = 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}'
        m = StaticMap(800, 600, padding_x=50, padding_y=50, url_template=url_template)

        # Override zoom para pruebas cortas
        from staticmap.staticmap import _lon_to_x, _lat_to_y

        def custom_zoom():
            for z in range(20, -1, -1):
                extent = m.determine_extent(zoom=z)
                width = (_lon_to_x(extent[2], z) - _lon_to_x(extent[0], z)) * m.tile_size
                if width > (m.width - m.padding[0] * 2):
                    continue
                height = (_lat_to_y(extent[1], z) - _lat_to_y(extent[3], z)) * m.tile_size
                if height > (m.height - m.padding[1] * 2):
                    continue
                return z
            return 0

        m._calculate_zoom = custom_zoom

        # Colormap
        vmin, vmax = np.min(velocities), np.max(velocities)
        if vmax == vmin:
            vmax = vmin + 1
        cmap = plt.get_cmap('jet')
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

        # Segmentos de línea coloreados
        for i in range(len(lats) - 1):
            speed_avg = (velocities[i] + velocities[i + 1]) / 2
            rgba = cmap(norm(speed_avg))
            hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))
            coords = [(lons[i], lats[i]), (lons[i+1], lats[i+1])]
            m.add_line(Line(coords, hex_color, 4))

        # Renderizar mapa con reintentos
        image = None
        for attempt in range(3):
            try:
                image = m.render()
                break
            except Exception as ex:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    print(f"Error al descargar cuadrículas de mapa GPS: {ex}")

        if image is None:
            return None

        # Agregar leyenda de colores con matplotlib
        fig, (ax_map, ax_cb) = plt.subplots(1, 2, figsize=(10, 6),
                                             gridspec_kw={'width_ratios': [20, 1]})
        ax_map.imshow(image)
        ax_map.axis('off')

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cb = plt.colorbar(sm, cax=ax_cb)
        cb.set_label('Speed (km/h)')

        return save_to_buffer(fig)

    except Exception as e:
        print(f"Error generando mapa GPS: {e}")
        return None


def plot_gps_route_simple(df, title=None, distance_m=0, slope_data=None):
    """
    Genera mapa GPS simple (sin mapa de calor), solo trazado de la ruta.
    Para contexto general de la prueba.
    slope_data: dict con slope_pct y angle_deg (opcional, para módulo de ascenso).
    """
    try:
        if not _check_internet():
            return None

        from staticmap import StaticMap, Line

        gps_data = prepare_gps_data(df)
        if gps_data is None:
            return None

        lats, lons, _ = gps_data

        url_template = 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}'
        m = StaticMap(800, 600, padding_x=50, padding_y=50, url_template=url_template)

        from staticmap.staticmap import _lon_to_x, _lat_to_y

        def custom_zoom():
            for z in range(20, -1, -1):
                extent = m.determine_extent(zoom=z)
                width = (_lon_to_x(extent[2], z) - _lon_to_x(extent[0], z)) * m.tile_size
                if width > (m.width - m.padding[0] * 2):
                    continue
                height = (_lat_to_y(extent[1], z) - _lat_to_y(extent[3], z)) * m.tile_size
                if height > (m.height - m.padding[1] * 2):
                    continue
                return z
            return 0

        m._calculate_zoom = custom_zoom

        # Línea azul gruesa
        coords = [(lons[i], lats[i]) for i in range(len(lats))]
        m.add_line(Line(coords, '#2196F3', 5))

        # Renderizar mapa con reintentos
        image = None
        for attempt in range(3):
            try:
                image = m.render()
                break
            except Exception as ex:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    print(f"Error al descargar cuadrículas de mapa simple: {ex}")

        if image is None:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(image)

        # Texto informativo
        info_lines = []
        if distance_m > 0:
            info_lines.append(f"Distance: {distance_m:.1f} m")
        if slope_data:
            info_lines.append(f"Slope: {slope_data['angle_deg']:.1f}° ({slope_data['slope_pct']:.1f}%)")

        if info_lines:
            info_text = "\n".join(info_lines)
            ax.text(0.02, 0.02, info_text, transform=ax.transAxes,
                    fontsize=12, bbox=dict(facecolor='white', alpha=0.8),
                    verticalalignment='bottom')

        ax.axis('off')

        return save_to_buffer(fig)

    except Exception as e:
        print(f"Error generando mapa simple: {e}")
        return None

