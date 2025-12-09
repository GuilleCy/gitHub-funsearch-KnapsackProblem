# my_greedy_heuristic_v1.py
from skeleton_knapsack import KnapsackSkeleton
import time

class MyGreedyHeuristic(KnapsackSkeleton):
    """
    Heurística voraz (greedy) basada en densidad valor/peso para el problema 0/1 knapsack.
    Hereda de KnapsackSkeleton y devuelve el dict esperado por solve().
    """

    def __init__(self, weights, values, capacity):
        super().__init__(weights, values, capacity)

    def heuristic(self, items_state):
        start_time = time.time()
        weights = items_state["weights"]
        values = items_state["values"]
        capacity = items_state["capacity"]

        # Calcular densidad (valor/peso)
        density = [v / w if w > 0 else 0 for v, w in zip(values, weights)]

        # Ordenar por densidad de mayor a menor
        sorted_indices = sorted(range(len(density)), key=lambda i: density[i], reverse=True)

        total_value = 0
        total_weight = 0
        selected_items = []

        # Seleccionar items mientras haya capacidad
        for i in sorted_indices:
            if total_weight + weights[i] <= capacity:
                selected_items.append(i)
                total_weight += weights[i]
                total_value += values[i]

        end_time = time.time()

        return {
            "items": selected_items,
            "total_value": total_value,
            "total_peso_usado": total_weight,
            "solve_time": end_time - start_time
        }
