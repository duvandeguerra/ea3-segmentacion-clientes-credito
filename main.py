from src.data_loader import HFDatasetLoader

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


if __name__ == "__main__":
    main()