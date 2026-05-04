"""
Gráficas de RPM vs tiempo.
"""
from plotting.base_plotter import save_to_buffer, get_figsize_from_cm
import matplotlib.pyplot as plt
from config import IMG_SIZE_DETAIL_SMALL, SAMPLE_INTERVAL_S


def plot_rpm_vs_time(event, title, benchmarks=None, figsize_cm=IMG_SIZE_DETAIL_SMALL):
    """
    Gráfica de RPM vs tiempo con etiquetas en puntos de referencia.
    """
    figsize = get_figsize_from_cm(*figsize_cm)
    fig, ax = plt.subplots(figsize=figsize)

    df = event['df']
    start_idx = event['metrics']['start_idx']

    try:
        start_pos = df.index.get_loc(start_idx)
    except KeyError:
        start_pos = 0

    df_reset = df.reset_index(drop=True)
    time_axis = (df_reset.index - start_pos) * SAMPLE_INTERVAL_S

    if 'RPM' not in df_reset.columns:
        ax.text(0.5, 0.5, "Sin datos de RPM", transform=ax.transAxes, ha='center')
        return save_to_buffer(fig)

    ax.plot(time_axis, df_reset['RPM'], label='RPM', color='purple')

    # Líneas de inicio y fin
    ax.axvline(x=0, color='#555555', linestyle='--', label='_nolegend_')

    if 'end_idx' in event['metrics']:
        end_idx = event['metrics']['end_idx']
        try:
            end_pos = df.index.get_loc(end_idx)
            t_end = (end_pos - start_pos) * SAMPLE_INTERVAL_S
            ax.axvline(x=t_end, color='#555555', linestyle='--', label='_nolegend_')
        except Exception:
            pass

    # Benchmarks opcionales (velocidad)
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
                    ax.axvline(x=t, color='#555555', linestyle='--', alpha=0.7)

                    if 'RPM' in df.columns:
                        rpm_val = df.loc[idx, 'RPM']
                        ax.text(t, rpm_val, f"{int(rpm_val)}", fontsize=9,
                                verticalalignment='bottom', horizontalalignment='right',
                                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        except Exception:
            pass

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("RPM")
    ax.set_title(title)
    ax.legend()
    ax.grid(True)

    return save_to_buffer(fig)
