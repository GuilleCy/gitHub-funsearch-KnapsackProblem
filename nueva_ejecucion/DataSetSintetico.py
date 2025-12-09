## DataSetSintetico
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle


# ---------- Clase generadora de muestras sintéticas ----------
class GeneradorMuestrasMochila:
    def __init__(self,
                 min_items=100,
                 max_items=2000,
                 step_items=50,
                 min_weight=10,
                 max_weight=50,
                 min_value=10,
                 max_value=50,
                 porcentaje_min=0.4,
                 porcentaje_max=0.8):
        self.min_items = min_items
        self.max_items = max_items
        self.step_items = step_items
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.min_value = min_value
        self.max_value = max_value
        self.porcentaje_min = porcentaje_min
        self.porcentaje_max = porcentaje_max
        self.df_muestras = None  # aquí se guarda el DataFrame generado

    def crear_muestras(self):
        muestras = []

        # Generamos una muestra por cada cantidad de ítems en el rango
        for i, num_items in enumerate(range(self.min_items, self.max_items + 1, self.step_items)):
            pesos = np.random.randint(self.min_weight, self.max_weight + 1, size=num_items)
            valores = np.random.randint(self.min_value, self.max_value + 1, size=num_items)
            suma_pesos = np.sum(pesos)

            capacidad = np.random.randint(
                int(self.porcentaje_min * suma_pesos),
                int(self.porcentaje_max * suma_pesos) + 1
            )

            muestra = {
                "muestra_id": i,
                "num_items": num_items,
                "capacidad": capacidad,
                "totalPeso": suma_pesos,
                "pesos": pesos.tolist(),
                "valores": valores.tolist()
            }
            muestras.append(muestra)

        self.df_muestras = pd.DataFrame(muestras)
        return self.df_muestras

    def save_as_pickle(self, folder_path: str):
        if self.df_muestras is None:
            raise ValueError("No se han generado muestras aún. Ejecuta crear_muestras() primero.")

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        hash_id = self.get_hash_id()

        # 🔹 Archivo 1: DataFrame solamente (seguro de cargar en cualquier script)
        df_path = os.path.join(folder_path, f"{hash_id}_df.pkl")
        with open(df_path, "wb") as f:
            pickle.dump(self.df_muestras, f)
        print(f"✅ DataFrame guardado como: {df_path}")

        # 🔹 Archivo 2: Objeto completo (requiere que el módulo sea importable)
        obj_path = os.path.join(folder_path, f"{hash_id}_obj.pkl")
        try:
            with open(obj_path, "wb") as f:
                pickle.dump(self, f)
            print(f"✅ Objeto completo guardado como: {obj_path}")
        except Exception as e:
            print(f"⚠️ No se pudo guardar el objeto completo (usa el DataFrame): {e}")

    def get_hash_id(self):
        return f"{self.min_items}_{self.max_items}_{self.step_items}"

    def graficar_crecimiento_muestras(self):
        if self.df_muestras is None:
            raise ValueError("No se han generado muestras aún. Ejecuta crear_muestras() primero.")

        plt.figure(figsize=(10, 5))
        plt.plot(self.df_muestras["muestra_id"], self.df_muestras["num_items"], marker='o', linestyle='-')
        plt.title("Crecimiento de la cantidad de ítems por muestra")
        plt.xlabel("ID de muestra")
        plt.ylabel("Número de ítems")
        plt.grid(True)
        plt.tight_layout()
        plt.show()




