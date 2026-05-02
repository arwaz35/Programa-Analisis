"""
Configuración base de matplotlib y funciones compartidas para gráficas.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io

# Estilo global
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'lines.linewidth': 1.5,
    'grid.alpha': 0.6,
    'grid.linestyle': ':',
})


def save_to_buffer(fig):
    """Guarda una figura matplotlib en un BytesIO buffer como PNG."""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf


def cm_to_inches(cm):
    """Convierte centímetros a pulgadas."""
    return cm / 2.54


def get_figsize_from_cm(width_cm, height_cm):
    """Retorna (width_inches, height_inches) desde centímetros."""
    return (cm_to_inches(width_cm), cm_to_inches(height_cm))
