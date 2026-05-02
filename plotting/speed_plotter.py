"""
Gráficas de velocidad vs tiempo.
"""
from plotting.base_plotter import save_to_buffer, get_figsize_from_cm
import matplotlib.pyplot as plt
from config import IMG_SIZE_SUMMARY, IMG_SIZE_DETAIL_VEL, SAMPLE_INTERVAL_S


def plot_speed_comparison(events, title, figsize_cm=IMG_SIZE_SUMMARY):
    """
    Gráfica comparativa de velocidad vs tiempo para múltiples eventos.
    Todos los eventos se alinean en t=0 al punto de inicio.
    """
    figsize = get_figsize_from_cm(*figsize_cm)
    fig, ax = plt.subplots(figsize=figsize)

    for i, event in enumerate(events):
        df = event['df']
        start_idx = event['metrics']['start_idx']

        try:
            start_pos = df.index.get_loc(start_idx)
        except KeyError:
            start_pos = 0

        df_reset = df.reset_index(drop=True)
        time_axis = (df_reset.index - start_pos) * SAMPLE_INTERVAL_S

        label = f"Evento {event.get('id', i+1)} ({event.get('pilot', '')})"
        ax.plot(time_axis, df_reset['Velocidad_GPS'], label=label)

    # Línea de inicio
    ax.axvline(x=0, color='#555555', linestyle='--', label='_nolegend_')

    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Velocidad (km/h)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True)

    return save_to_buffer(fig)


def plot_speed_detailed(event, title, benchmarks=None, figsize_cm=IMG_SIZE_DETAIL_VEL):
    """
    Gráfica detallada de velocidad vs tiempo del mejor evento,
    con marcas verticales en los benchmarks de velocidad.
    """
    figsize = get_figsize_from_cm(*figsize_cm)
    fig, ax = plt.subplots(figsize=figsize)

    df = event['df']
    start_idx = event['metrics']['start_idx']
    end_idx = event['metrics']['end_idx']

    try:
        start_pos = df.index.get_loc(start_idx)
        end_pos = df.index.get_loc(end_idx)
    except KeyError:
        start_pos = 0
        end_pos = len(df) - 1

    df_reset = df.reset_index(drop=True)
    time_axis = (df_reset.index - start_pos) * SAMPLE_INTERVAL_S

    ax.plot(time_axis, df_reset['Velocidad_GPS'], label='Velocidad', color='blue')

    # Líneas de inicio y fin
    ax.axvline(x=0, color='#555555', linestyle='--', label='_nolegend_')
    t_end = (end_pos - start_pos) * SAMPLE_INTERVAL_S
    ax.axvline(x=t_end, color='#555555', linestyle='--', label='_nolegend_')

    # Benchmarks opcionales
    if benchmarks:
        sub = df.iloc[start_pos:]
        for bm in benchmarks:
            if bm == 0:
                candidates = [start_idx]
            else:
                candidates = sub[sub['Velocidad_GPS'] >= bm].index.tolist()

            if candidates:
                idx = candidates[0]
                pos = df.index.get_loc(idx)
                t = (pos - start_pos) * SAMPLE_INTERVAL_S
                v = df.loc[idx, 'Velocidad_GPS']

                ax.axvline(x=t, color='#555555', linestyle='--', alpha=0.7)

                # Métricas acumuladas
                d_start = df.loc[start_idx, 'Distancia'] if 'Distancia' in df.columns else 0
                d_curr = df.loc[idx, 'Distancia'] if 'Distancia' in df.columns else 0
                cum_d = max(0, d_curr - d_start)

                slice_0_curr = df.loc[start_idx:idx]
                if 'Accel_X_ms2' in slice_0_curr.columns:
                    cum_a = slice_0_curr['Accel_X_ms2'].mean()
                else:
                    cum_a = (v / 3.6) / t if t > 0 else 0

                label_txt = f"{bm}km/h\nt:{t:.2f}s\nd:{cum_d:.2f}m\na:{cum_a:.2f}m/s²"
                y_txt = 10 + (benchmarks.index(bm) * 15)
                ax.text(t + 0.1, y_txt, label_txt, fontsize=9,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Velocidad (km/h)")
    ax.set_title(title)
    ax.grid(True)

    return save_to_buffer(fig)
