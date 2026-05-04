"""
Gráficas de aceleración vs tiempo.
"""
from plotting.base_plotter import save_to_buffer, get_figsize_from_cm
import matplotlib.pyplot as plt
from config import IMG_SIZE_DETAIL_SMALL, SAMPLE_INTERVAL_S


def plot_accel_vs_time(event, title, benchmarks=None, figsize_cm=IMG_SIZE_DETAIL_SMALL):
    """
    Gráfica de aceleración vs tiempo con promedio acumulado.
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

    if 'Accel_X_ms2' not in df_reset.columns:
        ax.text(0.5, 0.5, "Sin datos de aceleración", transform=ax.transAxes, ha='center')
        return save_to_buffer(fig)

    # Aceleración instantánea
    ax.plot(time_axis, df_reset['Accel_X_ms2'], label='Acceleration (m/s²)', color='blue')

    # Promedio acumulado (solo fase de análisis)
    braking_slice = df_reset.iloc[start_pos:end_pos + 1].copy()
    braking_slice['Cum_Avg'] = braking_slice['Accel_X_ms2'].expanding().mean()
    slice_time = time_axis[start_pos:end_pos + 1]
    ax.plot(slice_time, braking_slice['Cum_Avg'], label='Cumulative Avg', color='red', linestyle='--')

    # Líneas de referencia
    ax.axvline(x=0, color='#555555', linestyle='--', label='_nolegend_')
    t_end = (end_pos - start_pos) * SAMPLE_INTERVAL_S
    ax.axvline(x=t_end, color='#555555', linestyle='--', label='_nolegend_')

    # Benchmarks opcionales
    if benchmarks:
        try:
            sub = df.iloc[start_pos:]
            for bm in benchmarks:
                if bm == 0:
                    candidates = [start_idx]
                else:
                    candidates = sub[sub['Velocidad_GPS'] >= bm].index.tolist()
                if candidates:
                    idx = candidates[0]
                    t = (df.index.get_loc(idx) - start_pos) * SAMPLE_INTERVAL_S
                    if abs(t) > 0.05 and abs(t - t_end) > 0.05:
                        ax.axvline(x=t, color='#555555', linestyle='--', alpha=0.7)
        except Exception:
            pass

    # Anotación de promedio global
    avg_val = event['metrics']['avg_acc']
    ax.text(0.05, 0.95, f"Acc Avg: {avg_val:.2f} m/s²", transform=ax.transAxes,
            verticalalignment='top', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Acceleration (m/s²)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True)

    return save_to_buffer(fig)
