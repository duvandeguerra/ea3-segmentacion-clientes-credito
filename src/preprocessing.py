import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

TARGET_ORIGINAL = "default.payment.next.month"
PAY_COLS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL_COLS = [f"BILL_AMT{i}" for i in range(1, 7)]
PAY_AMT_COLS = [f"PAY_AMT{i}" for i in range(1, 7)]


class DataPreprocessor:
    """Limpia los datos, construye variables de comportamiento y las escala para K-means."""

    FEATURES = ["cupo_log", "utilizacion", "ratio_pago", "meses_con_retraso"]

    def __init__(self, percentil_recorte: float = 0.99):
        self.percentil_recorte = percentil_recorte
        self.scaler = StandardScaler()
        self.operaciones: list[str] = []

    # ---------- 1. Limpieza (reutilizada de EA2) ----------
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        filas_iniciales = len(df)

        df = df.drop(columns=["ID"])
        duplicados = int(df.duplicated().sum())
        df = df.drop_duplicates().reset_index(drop=True)
        df = df.drop(columns=["SEX"])
        df = df.rename(columns={TARGET_ORIGINAL: "default"})

        df["EDUCATION"] = df["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
        df["MARRIAGE"] = df["MARRIAGE"].replace({0: 3})

        montos = ["LIMIT_BAL"] + BILL_COLS + PAY_AMT_COLS
        df[montos] = df[montos].astype(float)

        self.operaciones += [
            "Se eliminó ID (identificador) y, sin él, se detectaron y eliminaron "
            f"{duplicados} filas duplicadas.",
            "Se eliminó SEX por consideraciones éticas (no discriminación).",
            "EDUCATION 0/5/6 -> 4 (otros) y MARRIAGE 0 -> 3 (otros): códigos no documentados.",
            "Montos unificados a float.",
            f"Filas: {filas_iniciales} -> {len(df)}.",
        ]
        return df

    # ---------- 2. Variables de comportamiento ----------
    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Facturas negativas (saldo a favor) cuentan como 0 consumo
        facturado = df[BILL_COLS].clip(lower=0)
        total_facturado = facturado.sum(axis=1)
        total_pagado = df[PAY_AMT_COLS].sum(axis=1)

        df["cupo_log"] = np.log1p(df["LIMIT_BAL"])

        df["utilizacion"] = facturado.mean(axis=1) / df["LIMIT_BAL"]
        tope = df["utilizacion"].quantile(self.percentil_recorte)
        recortados = int((df["utilizacion"] > tope).sum())
        max_original = df["utilizacion"].max()
        df["utilizacion"] = df["utilizacion"].clip(upper=tope)

        sin_consumo = int((total_facturado == 0).sum())
        df["ratio_pago"] = (total_pagado / total_facturado.replace(0, np.nan)).fillna(1.0)
        df["ratio_pago"] = df["ratio_pago"].clip(upper=1.0)

        df["meses_con_retraso"] = (df[PAY_COLS] > 0).sum(axis=1)
        df["retraso_maximo"] = df[PAY_COLS].clip(lower=0).max(axis=1)

        self.operaciones += [
            "cupo_log = log(1 + LIMIT_BAL): reduce el sesgo del cupo "
            f"(asimetría {df['LIMIT_BAL'].skew():.2f} -> {df['cupo_log'].skew():.2f}).",
            "utilizacion = factura promedio / cupo (facturas negativas = 0). "
            f"Recortada en el percentil {self.percentil_recorte * 100:.0f} ({tope:.2f}): "
            f"{recortados} clientes afectados; el máximo original era {max_original:.2f}.",
            "ratio_pago = total pagado / total facturado (6 meses), con tope 1.0. "
            f"{sin_consumo} clientes sin consumo reciben 1.0 (sin deuda pendiente).",
            "meses_con_retraso = meses (de 6) con PAY_x > 0.",
            "retraso_maximo = mayor PAY_x (valores negativos = 0, sin retraso).",
        ]

        corr = df["meses_con_retraso"].corr(df["retraso_maximo"])
        self.operaciones.append(
            f"retraso_maximo no entra al clustering: correlación {corr:.2f} con "
            "meses_con_retraso (miden el mismo concepto y el retraso pesaría el doble). "
            "Se conserva para describir los segmentos."
        )

        return df

    # ---------- 3. Escalado ----------
    def scale(self, df: pd.DataFrame) -> np.ndarray:
        X = self.scaler.fit_transform(df[self.FEATURES])
        self.operaciones.append(
            "StandardScaler sobre las 4 variables: K-means usa distancias y sin escalar "
            "el cupo dominaría los grupos. Al no ser supervisado, no hay división "
            "train/test y el escalador se ajusta con todos los datos."
        )
        return X