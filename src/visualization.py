from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # sin ventana: necesario en GitHub Actions
import matplotlib.pyplot as plt


def plot_seleccion_k(tabla, path: str) -> str:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    metricas = [
        ("inercia", "Inercia (codo)", "menor es mejor"),
        ("silueta", "Coeficiente de silueta", "mayor es mejor"),
        ("davies_bouldin", "Davies-Bouldin", "menor es mejor"),
    ]
    for ax, (col, titulo, nota) in zip(axes, metricas):
        ax.plot(tabla["k"], tabla[col], marker="o")
        ax.set_title(f"{titulo}\n({nota})")
        ax.set_xlabel("Número de segmentos (k)")
        ax.set_xticks(tabla["k"])
        ax.grid(alpha=0.3)
    fig.suptitle("Selección del número de segmentos")
    fig.tight_layout()

    ruta = Path(path)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=120)
    plt.close(fig)
    return str(ruta)