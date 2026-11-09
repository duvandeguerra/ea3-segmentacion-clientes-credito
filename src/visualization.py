from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # sin ventana: necesario en GitHub Actions
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA


def _guardar(fig, path: str) -> str:
    ruta = Path(path)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    plt.close(fig)
    return ruta.as_posix()


def _etiquetas(nombres: dict[int, str]) -> list[str]:
    return [f"{seg}: {nombre}" for seg, nombre in nombres.items()]


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
    return _guardar(fig, path)


def plot_segmentos_pca(X, labels, nombres, path: str,
                       muestra: int = 5000, random_state: int = 42) -> str:
    """Proyecta las 4 variables a 2 dimensiones para poder ver los segmentos."""
    pca = PCA(n_components=2, random_state=random_state)
    coords = pca.fit_transform(X)
    idx = np.random.default_rng(random_state).choice(len(X), size=min(muestra, len(X)), replace=False)

    fig, ax = plt.subplots(figsize=(9, 6))
    for seg, etiqueta in zip(nombres, _etiquetas(nombres)):
        mask = labels[idx] == seg
        ax.scatter(coords[idx][mask, 0], coords[idx][mask, 1], s=8, alpha=0.5, label=etiqueta)
    var = pca.explained_variance_ratio_
    ax.set_xlabel(f"Componente principal 1 ({var[0]:.0%} de la varianza)")
    ax.set_ylabel(f"Componente principal 2 ({var[1]:.0%} de la varianza)")
    ax.set_title(f"Segmentos de clientes (muestra de {len(idx)} clientes, proyección PCA)")
    ax.legend(markerscale=3)
    ax.grid(alpha=0.3)
    return _guardar(fig, path)


def plot_perfil_segmentos(centros, features, nombres, path: str) -> str:
    """Mapa de calor: cuánto se aleja cada segmento del promedio en cada variable."""
    fig, ax = plt.subplots(figsize=(9, 1 + 0.9 * len(nombres)))
    im = ax.imshow(centros, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
    ax.set_xticks(range(len(features)))
    ax.set_xticklabels(features)
    ax.set_yticks(range(len(nombres)))
    ax.set_yticklabels(_etiquetas(nombres))
    for i in range(centros.shape[0]):
        for j in range(centros.shape[1]):
            ax.text(j, i, f"{centros[i, j]:+.2f}", ha="center", va="center", fontsize=10)
    fig.colorbar(im, ax=ax, label="Desviaciones estándar respecto al promedio")
    ax.set_title("Perfil de cada segmento (rojo = por encima del promedio, azul = por debajo)")
    return _guardar(fig, path)


def plot_incumplimiento(perfil, nombres, tasa_global: float, path: str) -> str:
    """Validación externa: tasa de incumplimiento por segmento (default no se usó en el modelo)."""
    fig, ax = plt.subplots(figsize=(9, 5))
    barras = ax.bar(_etiquetas(nombres), perfil["tasa_incumplimiento"] * 100)
    ax.bar_label(barras, fmt="%.1f%%")
    ax.axhline(tasa_global * 100, linestyle="--", color="gray",
               label=f"Promedio general ({tasa_global:.1%})")
    ax.set_ylabel("% de clientes que incumplen el mes siguiente")
    ax.set_title("Tasa de incumplimiento por segmento")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    return _guardar(fig, path)