from src.data_loader import HFDatasetLoader
from src.preprocessing import DataPreprocessor

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


if __name__ == "__main__":
    main()