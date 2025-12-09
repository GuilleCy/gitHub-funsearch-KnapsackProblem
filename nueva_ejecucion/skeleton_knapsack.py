# skeleton_knapsack.py
import time

class KnapsackSkeleton:
    """
    Esqueleto para resolver el problema de la mochila mediante heurísticas.
    No utiliza Pyomo ni MILP. Su propósito es definir la estructura base que
    las heurísticas (como MyGreedyHeuristic o las generadas por FunSearch)
    deben extender e implementar.
    """

    def __init__(self, weights, values, capacity):
        self.weights = weights
        self.values = values
        self.capacity = capacity
        self.solution_items = []
        self.total_value = 0
        self.total_weight = 0

    def heuristic(self, items_state):
        """
        Función heurística a implementar por la subclase o generada por FunSearch.
        items_state es un diccionario con:
            - "weights": lista de pesos
            - "values": lista de valores
            - "capacity": capacidad total (float o int)
        Debe devolver un diccionario con:
            - "items": índices seleccionados
            - "total_value": valor total obtenido
            - "total_peso_usado": peso total
            - "solve_time": tiempo de ejecución
        """
        raise NotImplementedError("Debe implementarse la función 'heuristic' en la subclase o módulo generado.")

    def solve(self):
        """
        Ejecuta la heurística definida por el usuario o generada por FunSearch.
        Incluye protección contra errores de tipo y modificaciones indebidas.
        """
        start_time = time.time()

        # 🔒 Crear una copia segura del estado de los ítems
        items_state = {
            "weights": list(self.weights),
            "values": list(self.values),
            "capacity": float(self.capacity)
        }

        try:
            resultado = self.heuristic(items_state)

            # Validación del tipo de salida
            if not isinstance(resultado, dict):
                raise TypeError("La heurística no devolvió un diccionario.")

        except Exception as e:
            print(f"❌ Error al evaluar heurística: {e}")
            return {
                "items": [],
                "total_value": 0,
                "total_peso_usado": 0,
                "solve_time": time.time() - start_time,
                "error": str(e)
            }

        end_time = time.time()

        # Asegurar que la salida tenga las claves esperadas
        resultado.setdefault("items", [])
        resultado.setdefault("total_value", 0)
        resultado.setdefault("total_peso_usado", 0)
        resultado["solve_time"] = end_time - start_time

        # Guardar resultados internos
        self.solution_items = resultado["items"]
        self.total_value = resultado["total_value"]
        self.total_weight = resultado["total_peso_usado"]

        return resultado

    def create_model(self):
        """
        Método placeholder para compatibilidad con FunSearch.
        Algunas heurísticas o configuraciones podrían intentar invocarlo.
        """
        return None
