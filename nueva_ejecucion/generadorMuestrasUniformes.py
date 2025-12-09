## generadorMuestrasUniformes.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle

# ---------- Clase revisada para generar muestras aleatorias ----------
class GeneradorLotesMochila:
    def __init__(self,
                 min_weight=1,
                 max_weight=50,
                 min_value=1,
                 max_value=50,
                 porc_min=0.4,
                 porc_max=0.7):
        """
        min_weight / max_weight : rango de pesos por ítem
        min_value / max_value   : rango de valores por ítem
        porc_min / porc_max     : porcentaje de la suma de pesos para la capacidad
        """
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.min_value = min_value
        self.max_value = max_value
        self.porc_min = porc_min
        self.porc_max = porc_max
        self.tabla_muestras = None

    def generar_lotes(self, n_lotes: int, items_por_lote: int) -> pd.DataFrame:
        """
        Crea 'n_lotes' muestras, cada una con 'items_por_lote' ítems.
        """
        registros = []
        for i in range(n_lotes):
            pesos = np.random.randint(self.min_weight, self.max_weight + 1, size=items_por_lote)
            valores = np.random.randint(self.min_value, self.max_value + 1, size=items_por_lote)
            peso_total = np.sum(pesos)

            capacidad = np.random.randint(
                int(self.porc_min * peso_total),
                int(self.porc_max * peso_total) + 1
            )

            registros.append({
                "lote_id": i,
                "num_items": items_por_lote,
                "capacidad": capacidad,
                "total_pesos": peso_total,
                "pesos": pesos.tolist(),
                "valores": valores.tolist()
            })

        self.tabla_muestras = pd.DataFrame(registros)
        return self.tabla_muestras

    def guardar_pickle(self, carpeta: str):
        """
        Guarda el DataFrame y, opcionalmente, el objeto completo en archivos .pkl
        """
        if self.tabla_muestras is None:
            raise ValueError("Primero debes generar los lotes con generar_lotes().")

        os.makedirs(carpeta, exist_ok=True)
        nombre_base = f"lotes_{len(self.tabla_muestras)}"

        # DataFrame
        df_path = os.path.join(carpeta, f"{nombre_base}_df.pkl")
        with open(df_path, "wb") as f:
            pickle.dump(self.tabla_muestras, f)
        print(f"✅ DataFrame guardado en: {df_path}")

        # Objeto completo (opcional)
        obj_path = os.path.join(carpeta, f"{nombre_base}_obj.pkl")
        try:
            with open(obj_path, "wb") as f:
                pickle.dump(self, f)
            print(f"✅ Objeto completo guardado en: {obj_path}")
        except Exception as e:
            print(f"⚠️ No se pudo guardar el objeto completo: {e}")

    def graficar_lotes(self):
        """
        Gráfico de barras con el número de ítems de cada lote.
        """
        if self.tabla_muestras is None:
            raise ValueError("No hay datos para graficar. Ejecuta generar_lotes() primero.")

        plt.figure(figsize=(8, 5))
        plt.bar(self.tabla_muestras["lote_id"], self.tabla_muestras["num_items"], alpha=0.8)
        plt.title("Número de ítems por lote generado")
        plt.xlabel("ID del lote")
        plt.ylabel("Cantidad de ítems")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

    def get_hash_id(self):
        return f"{self.min_items}_{self.max_items}_{self.step_items}"



