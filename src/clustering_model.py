import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score
import numpy as np


class ClusteringModel:
    """K-means: selección de k con evidencia y entrenamiento del modelo final."""

    def __init__(self, k_min: int = 2, k_max: int = 8, random_state: int = 42,
                 n_init: int = 10, silhouette_sample: int = 10_000):
        self.k_range = range(k_min, k_max + 1)
        self.random_state = random_state
        self.n_init = n_init
        self.silhouette_sample = silhouette_sample
        self.tabla_k: pd.DataFrame | None = None
        self.model: KMeans | None = None
        self.metrics: dict[str, float] = {}

    def _kmeans(self, k: int) -> KMeans:
        return KMeans(n_clusters=k, n_init=self.n_init, random_state=self.random_state)

    def _silueta(self, X, labels) -> float:
        # Con 30.000 clientes la silueta completa es muy costosa: se usa una muestra fija
        return silhouette_score(X, labels, sample_size=self.silhouette_sample,
                                random_state=self.random_state)

    def evaluate_k(self, X) -> pd.DataFrame:
        filas = []
        for k in self.k_range:
            modelo = self._kmeans(k).fit(X)
            filas.append({
                "k": k,
                "inercia": modelo.inertia_,
                "silueta": self._silueta(X, modelo.labels_),
                "davies_bouldin": davies_bouldin_score(X, modelo.labels_),
            })
        self.tabla_k = pd.DataFrame(filas)
        return self.tabla_k

    def fit(self, X, k: int, orden_col: int | None = None):
        self.model = self._kmeans(k).fit(X)
        labels = self.model.labels_

        # Los números de cluster son arbitrarios (pueden cambiar entre ejecuciones).
        # Se renumeran según una variable para que el segmento 0 sea siempre el de menor valor.
        if orden_col is not None:
            orden = np.argsort(self.model.cluster_centers_[:, orden_col])
            rango = np.empty(k, dtype=int)
            rango[orden] = np.arange(k)
            labels = rango[labels]                        
            self.centros_ = self.model.cluster_centers_[orden]
        else:
            self.centros_ = self.model.cluster_centers_

        self.labels_ = labels
        self.metrics = {
            "k": k,
            "inercia": self.model.inertia_,
            "silueta": self._silueta(X, labels),
            "davies_bouldin": davies_bouldin_score(X, labels),
            "iteraciones": self.model.n_iter_,
        }
        return labels

    @staticmethod
    def profile(df: pd.DataFrame, labels) -> pd.DataFrame:
        """Describe cada segmento en unidades de negocio (no en la escala estandarizada)."""
        d = df.assign(segmento=labels)
        perfil = d.groupby("segmento").agg(
            clientes=("segmento", "size"),
            cupo_promedio=("LIMIT_BAL", "mean"),
            utilizacion=("utilizacion", "mean"),
            ratio_pago=("ratio_pago", "mean"),
            meses_con_retraso=("meses_con_retraso", "mean"),
            retraso_maximo=("retraso_maximo", "mean"),
            edad_promedio=("AGE", "mean"),
            tasa_incumplimiento=("default", "mean"),
            incumplimientos=("default", "sum"),
        )
        perfil.insert(1, "porcentaje", perfil["clientes"] / len(d) * 100)
        perfil["pct_del_total_incumplimientos"] = (
            perfil["incumplimientos"] / perfil["incumplimientos"].sum() * 100
        )
        
        return perfil

    @staticmethod
    def name_segments(perfil: pd.DataFrame) -> dict[int, str]:
        """Asigna nombres de negocio con reglas sobre el perfil (no fijos a mano)."""
        nombres = {}
        restantes = perfil.copy()

        moroso = restantes["meses_con_retraso"].idxmax()
        nombres[moroso] = "Morosos recurrentes"
        restantes = restantes.drop(moroso)

        pagadores = restantes["ratio_pago"].idxmax()
        nombres[pagadores] = "Bajo uso, pagan el total"
        restantes = restantes.drop(pagadores)

        if len(restantes) == 2:
            alto = restantes["cupo_promedio"].idxmax()
            nombres[alto] = "Revolventes de cupo alto"
            nombres[restantes.drop(alto).index[0]] = "Revolventes de cupo bajo"
        else:
            for seg in restantes.index:
                nombres[seg] = "Revolventes"
        return dict(sorted(nombres.items()))
    
    @property
    def params(self) -> dict:
        return self.model.get_params()