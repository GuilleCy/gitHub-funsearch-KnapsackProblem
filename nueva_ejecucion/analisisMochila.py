#analisisMochila.py
import os
import pickle
import matplotlib.pyplot as plt
from Ejercicio_KP.Solver_OR_tools import SolverMochila
import numpy as np


class EvaluadorMochila:
    def __init__(self, df_muestras, hash_id_func=None):
        if df_muestras is None:
            raise ValueError("Debes proporcionar un DataFrame de muestras válido.")
        self.df_muestras = df_muestras
        self.get_hash_id = hash_id_func if hash_id_func else lambda: "default"

    def resolver_muestras(self):
        """Resuelve cada muestra con OR-Tools y agrega las métricas al DataFrame."""
        tiempos = []
        valores_totales = []
        pesos_totales = []
        num_items_solucion = []

        for _, row in self.df_muestras.iterrows():
            solver = SolverMochila(
                values=row["valores"],
                weights=[row["pesos"]],       # OR-Tools espera lista de listas
                capacities=[row["capacidad"]]
            )
            solver.resolver()
            resultado = solver.obtener_resultado()

            # === Ajusta estos nombres si tu SolverMochila usa otros ===
            tiempos.append(resultado["tiempo_segundos"])
            valores_totales.append(resultado["valor_total"])
            pesos_totales.append(resultado["peso_total"])
            num_items_solucion.append(resultado["num_items_seleccionados"])

        # Agregar columnas sin espacios extra
        self.df_muestras["tiempo_segundos"] = tiempos
        self.df_muestras["valor_total"] = valores_totales
        self.df_muestras["peso_total"] = pesos_totales
        self.df_muestras["num_items_seleccionados"] = num_items_solucion

        return self.df_muestras

    def graficar_resultados(self):
        if self.df_muestras is None or "tiempo_segundos" not in self.df_muestras.columns:
            raise ValueError("Primero debes ejecutar resolver_muestras()")

        num_muestras = len(self.df_muestras)
        indices = np.arange(num_muestras)

        capacidades = self.df_muestras["capacidad"]
        pesos_usados = self.df_muestras["peso_total"]
        valores_obtenidos = self.df_muestras["valor_total"]
        valores_por_muestra = self.df_muestras["valores"]

        # Comparaciones con la suma total
        valores_totales = [np.sum(v) for v in valores_por_muestra]
        setenta_cinco = [v * 0.75 for v in valores_totales]
        cincuenta = [v * 0.50 for v in valores_totales]

        fig, axs = plt.subplots(1, 3, figsize=(20, 4))

        # 1) Tiempo vs número de ítems
        axs[0].plot(self.df_muestras["num_items"],
                    self.df_muestras["tiempo_segundos"],
                    marker="o", linestyle="-")
        axs[0].set_title("Tiempo de resolución vs número de ítems (log)")
        axs[0].set_xlabel("Número de ítems")
        axs[0].set_ylabel("Tiempo (s)")
        axs[0].set_yscale("log")
        axs[0].grid(True, which="both", linestyle="--", linewidth=0.5)

        # 2) Capacidad vs Peso usado
        width = 0.35
        axs[1].bar(indices - width / 2, capacidades, width, label="Capacidad", alpha=0.7)
        axs[1].bar(indices + width / 2, pesos_usados, width, label="Peso utilizado", alpha=0.7)
        axs[1].set_title("Capacidad vs Peso total usado")
        axs[1].set_xlabel("ID de muestra")
        axs[1].set_ylabel("Capacidad")
        axs[1].set_xticks(indices)
        axs[1].set_xticklabels(self.df_muestras["muestra_id"], rotation=45)
        axs[1].legend()
        axs[1].grid(True)

        # 3) Valor obtenido vs proporciones
        axs[2].plot(indices, valores_obtenidos, label="Valor obtenido", marker="o")
        axs[2].plot(indices, setenta_cinco, label="75% del valor total", linestyle="--")
        axs[2].plot(indices, cincuenta, label="50% del valor total", linestyle="--")
        axs[2].set_title("Valor obtenido vs proporciones del valor total")
        axs[2].set_xlabel("ID de muestra")
        axs[2].set_ylabel("Valor")
        axs[2].set_xticks(indices)
        axs[2].set_xticklabels(self.df_muestras["muestra_id"], rotation=45)
        axs[2].legend()
        axs[2].grid(True)

        plt.tight_layout()
        plt.show()

    def save_resultados_pickle(self, folder_path: str):
        if self.df_muestras is None:
            raise ValueError("No hay muestras para guardar")

        hash_id = self.get_hash_id()
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, f"{hash_id}_resultados.pkl")
        with open(file_path, "wb") as f:
            pickle.dump(self.df_muestras, f)
        print(f"Resultados guardados en: {file_path}")
