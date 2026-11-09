from src.data_loader import HFDatasetLoader
from src.preprocessing import DataPreprocessor
from src.clustering_model import ClusteringModel
from src.visualization import (
    plot_incumplimiento, plot_perfil_segmentos, plot_segmentos_pca, plot_seleccion_k,
)

DATASET_ID = "scikit-learn/credit-card-clients"
PREGUNTA_NEGOCIO = (
    "¿Qué perfiles de clientes existen según su comportamiento de uso y pago de la tarjeta, "
    "para que el área de riesgo crediticio defina políticas diferenciadas por segmento?"
)


def main():
    print("PREGUNTA DE NEGOCIO:\n", PREGUNTA_NEGOCIO, "\n")
    print(f"Dataset: {DATASET_ID}")
    print(f"Enlace: https://huggingface.co/datasets/{DATASET_ID}\n")

    df = HFDatasetLoader(DATASET_ID, split="train").load()

    print("Dimensiones:", df.shape)
    print("\nTipos de datos:\n", df.dtypes.to_string())
    print("\nNulos totales:", int(df.isnull().sum().sum()))
    print("\nMuestra:\n", df.head().to_string())

    # ---------- PREPROCESAMIENTO ----------
    print("\n" + "=" * 60 + "\nPREPROCESAMIENTO\n" + "=" * 60)
    prep = DataPreprocessor(percentil_recorte=0.99)
    df_limpio = prep.clean(df)
    df_feat = prep.build_features(df_limpio)
    feats = DataPreprocessor.FEATURES

    print("ANTES:", df.shape, "-> DESPUÉS de limpiar:", df_limpio.shape)

    print("\nVariables de comportamiento (escala original):")
    print(df_feat[feats].describe().round(3).to_string())

    print("\nDesviación estándar ANTES de escalar (evidencia de escalas muy distintas):")
    print(df_feat[["LIMIT_BAL"] + feats].std().round(3).to_string())

    print("\nCorrelación entre variables de comportamiento:")
    print(df_feat[feats].corr().round(2).to_string())

    X = prep.scale(df_feat)
    print("\nDESPUÉS de escalar -> medias:", X.mean(axis=0).round(3), " desv:", X.std(axis=0).round(3))

    print("\nRegistro de operaciones:")
    for op in prep.operaciones:
        print(" -", op)

    # ---------- SELECCIÓN DE k ----------
    print("\n" + "=" * 60 + "\nSELECCIÓN DEL NÚMERO DE SEGMENTOS (k)\n" + "=" * 60)
    modelo = ClusteringModel(k_min=2, k_max=8, random_state=42)
    tabla_k = modelo.evaluate_k(X)
    print(tabla_k.round(3).to_string(index=False))
    print("\nGráfica:", plot_seleccion_k(tabla_k, "outputs/seleccion_k.png"))

    # ---------- COMPARACIÓN k = 3 vs k = 4 ----------
    idx_retraso = DataPreprocessor.FEATURES.index("meses_con_retraso")
    for k in (3, 4):
        labels = modelo.fit(X, k, orden_col=idx_retraso)
        m = modelo.metrics
        print(f"\n--- k = {k} | silueta {m['silueta']:.3f} | Davies-Bouldin {m['davies_bouldin']:.3f} ---")
        print(ClusteringModel.profile(df_feat, labels).round(3).to_string())

    # ---------- MODELO FINAL ----------
    K_ELEGIDO = 4
    print("\n" + "=" * 60 + f"\nMODELO FINAL: K-means con k = {K_ELEGIDO}\n" + "=" * 60)
    labels = modelo.fit(X, K_ELEGIDO, orden_col=idx_retraso)
    perfil = ClusteringModel.profile(df_feat, labels)
    nombres = ClusteringModel.name_segments(perfil)
    perfil.insert(0, "nombre", perfil.index.map(nombres))

    print("Parámetros:", modelo.params)
    print("Métricas:", {k: round(v, 3) for k, v in modelo.metrics.items()})
    print("\nPerfil de segmentos:\n", perfil.round(3).to_string())

    tasa_global = df_feat["default"].mean()
    print("\nGráficas:")
    print(" -", plot_segmentos_pca(X, labels, nombres, "outputs/segmentos_pca.png"))
    print(" -", plot_perfil_segmentos(modelo.centros_, DataPreprocessor.FEATURES, nombres,
                                      "outputs/perfil_segmentos.png"))
    print(" -", plot_incumplimiento(perfil, nombres, tasa_global, "outputs/incumplimiento_segmentos.png"))

if __name__ == "__main__":
    main()