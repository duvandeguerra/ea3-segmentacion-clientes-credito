from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Genera el resumen .txt de la ejecución a partir de los objetos ya calculados."""

    SEP = "=" * 78

    def __init__(self, pregunta, dataset_id, split, forma_inicial, forma_final,
                 operaciones, features, modelo, tabla_k, perfil, tasa_global, graficas):
        self.pregunta = pregunta
        self.dataset_id = dataset_id
        self.split = split
        self.forma_inicial = forma_inicial
        self.forma_final = forma_final
        self.operaciones = operaciones
        self.features = features
        self.modelo = modelo
        self.tabla_k = tabla_k
        self.perfil = perfil
        self.tasa_global = tasa_global
        self.graficas = graficas

    @staticmethod
    def _titulo(texto: str) -> list[str]:
        return ["", texto, "-" * 78]

    def _encabezado(self) -> list[str]:
        return [
            self.SEP,
            "RESUMEN DE EJECUCIÓN - SEGMENTACIÓN DE CLIENTES CON K-MEANS",
            self.SEP,
            f"Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M:%S}",
        ]

    def _pregunta(self) -> list[str]:
        return self._titulo("1. PREGUNTA DE NEGOCIO") + [
            self.pregunta,
            "Quién la necesita: área de riesgo crediticio y de producto de tarjetas.",
            "Decisión que apoya: qué política aplicar a cada segmento (fidelización, "
            "activación, alertas preventivas o cobranza).",
        ]

    def _dataset(self) -> list[str]:
        return self._titulo("2. DATASET") + [
            f"Identificador: {self.dataset_id}",
            f"Enlace: https://huggingface.co/datasets/{self.dataset_id}",
            f"Split: {self.split}",
            "Contenido: 6 meses (abr-sep 2005) de cupo, facturas, pagos y retrasos de "
            "clientes de tarjetas de crédito en Taiwán.",
            f"Dimensiones originales: {self.forma_inicial[0]} filas x {self.forma_inicial[1]} columnas",
            f"Dimensiones tras limpieza: {self.forma_final[0]} filas x {self.forma_final[1]} columnas",
        ]

    def _preprocesamiento(self) -> list[str]:
        return self._titulo("3. PREPROCESAMIENTO") + [f"- {op}" for op in self.operaciones]

    def _modelo(self) -> list[str]:
        p = self.modelo.params
        return self._titulo("4. MODELO") + [
            "Tipo de aprendizaje: NO SUPERVISADO. No existe una etiqueta de 'tipo de cliente';",
            "los segmentos se descubren a partir del comportamiento.",
            "Algoritmo: K-means (scikit-learn).",
            f"Variables del clustering ({len(self.features)}): {', '.join(self.features)}",
            "No usadas en el clustering: default (reservada para validación externa), "
            "AGE/EDUCATION/MARRIAGE (solo para describir), SEX (ética), retraso_maximo (redundante).",
            f"Parámetros: {p}",
            f"Configuración: k evaluado de {self.tabla_k['k'].min()} a {self.tabla_k['k'].max()}, "
            f"random_state={p['random_state']}, n_init={p['n_init']}, silueta calculada "
            f"sobre una muestra de {self.modelo.silhouette_sample} clientes.",
        ]

    def _seleccion_k(self) -> list[str]:
        t = self.tabla_k
        k_sil = int(t.loc[t["silueta"].idxmax(), "k"])
        k = self.modelo.metrics["k"]
        return self._titulo("5. SELECCIÓN DEL NÚMERO DE SEGMENTOS") + [
            t.round(3).to_string(index=False),
            "",
            f"Mayor silueta: k = {k_sil}. k elegido: {k}.",
            "Criterios: método del codo, silueta, Davies-Bouldin y validación externa con la",
            "tasa de incumplimiento por segmento (ver sección 7).",
        ]

    def _metricas(self) -> list[str]:
        m = self.modelo.metrics
        return self._titulo("6. MÉTRICAS DEL MODELO FINAL") + [
            f"k: {m['k']}",
            f"Inercia: {m['inercia']:,.1f}",
            f"Coeficiente de silueta: {m['silueta']:.3f}",
            f"Davies-Bouldin: {m['davies_bouldin']:.3f}",
            f"Iteraciones hasta converger: {m['iteraciones']}",
        ]

    def _segmentos(self) -> list[str]:
        p = self.perfil
        mayor = p["tasa_incumplimiento"].idxmax()
        menor = p["tasa_incumplimiento"].idxmin()
        veces = p.loc[mayor, "tasa_incumplimiento"] / p.loc[menor, "tasa_incumplimiento"]
        return self._titulo("7. PERFIL DE SEGMENTOS Y VALIDACIÓN EXTERNA") + [
            p.round(3).to_string(),
            "",
            f"Tasa de incumplimiento general: {self.tasa_global:.1%}.",
            f"Rango por segmento: {p.loc[menor, 'tasa_incumplimiento']:.1%} "
            f"({p.loc[menor, 'nombre']}) a {p.loc[mayor, 'tasa_incumplimiento']:.1%} "
            f"({p.loc[mayor, 'nombre']}).",
            f"El segmento de mayor riesgo incumple {veces:.1f} veces más que el de menor riesgo.",
            "Como 'default' no se usó para formar los grupos, esta diferencia indica que los",
            "segmentos capturan diferencias reales de riesgo.",
        ]

    def _graficas(self) -> list[str]:
        return self._titulo("8. GRÁFICAS GENERADAS") + [f"- {g}" for g in self.graficas]

    def build(self) -> str:
        partes = (self._encabezado() + self._pregunta() + self._dataset()
                  + self._preprocesamiento() + self._modelo() + self._seleccion_k()
                  + self._metricas() + self._segmentos() + self._graficas())
        return "\n".join(partes)

    def save(self, path: str) -> str:
        ruta = Path(path)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(self.build(), encoding="utf-8")
        return str(ruta)