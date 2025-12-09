# ============================================================
# funsearch_loop_evolutivo.py
# ============================================================

import os
import re
import ast
import random
import pickle
import pandas as pd
import numpy as np
import threading
import time
import matplotlib.pyplot as plt
from datetime import datetime
from importlib.machinery import SourceFileLoader

from rich.jupyter import display

from gemini_cliente import Gemini
from skeleton_knapsack import KnapsackSkeleton


# ============================================================
# 1️⃣ Cargar base desde pickle
# ============================================================
def cargar_base_pickle(ruta: str) -> pd.DataFrame:
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
    with open(ruta, "rb") as f:
        df = pickle.load(f)
    if not isinstance(df, pd.DataFrame):
        raise TypeError("El archivo cargado no es un DataFrame válido.")
    print(f"✅ Base cargada correctamente ({len(df)} registros)")
    return df


# ============================================================
# 2️⃣ Evaluador de heurística (score normalizado multi-métrica)
#    + guarda resultados por instancia
# ============================================================
def evaluate_candidate(code: str, df_base: pd.DataFrame, iteracion: int, carpeta_salida: str):
    import tempfile

    os.makedirs(carpeta_salida, exist_ok=True)
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, "candidate.py")


    with open(tmp_path, "w", encoding="utf-8") as f:
        # Agregar imports básicos preventivos antes del código generado
        f.write("import math\nimport random\nimport time\nimport numpy as np\n")
        f.write(code)

    try:
        # Cargar módulo temporal con la heurística generada
        candidate_module = SourceFileLoader("candidate", tmp_path).load_module()
        if not hasattr(candidate_module, "heuristic"):
            raise AttributeError("El módulo candidato no contiene 'heuristic'.")

        eficiencias, tiempos, valores = [], [], []

        # Evaluar heurística sobre todas las instancias
        for _, row in df_base.iterrows():
            skeleton = KnapsackSkeleton(
                weights=row['pesos'],
                values=row['valores'],
                capacity=row['capacidad']
            )
            skeleton.heuristic = candidate_module.heuristic
            skeleton.create_model()
            res = skeleton.solve()

            capacidad = row['capacidad']
            peso_usado = res['total_peso_usado']
            valor_total = res['total_value']
            tiempo = res['solve_time']

            eficiencia = (capacidad - peso_usado) / capacidad
            eficiencias.append(eficiencia)
            tiempos.append(tiempo)
            valores.append(valor_total)

        # Normalización de métricas
        def minmax(x):
            x = np.array(x, dtype=float)
            if x.max() == x.min():
                return np.ones_like(x)
            return (x - x.min()) / (x.max() - x.min())

        norm_ef = 1 - minmax(eficiencias)  # menor espacio libre = mejor
        norm_ti = 1 - minmax(tiempos)      # menor tiempo = mejor
        norm_val = minmax(valores)         # mayor valor = mejor

        # Score por instancia
        score_por_instancia = norm_ef + norm_val
        df_scores = pd.DataFrame({
            "eficiencia": eficiencias,
            "tiempo": tiempos,
            "valor_total": valores,
            "score_instancia": score_por_instancia
        })

        # Promedio global del score
        score_final = df_scores["score_instancia"].mean()

        # Guardar detalle por instancia
        ruta_csv = os.path.join(carpeta_salida, f"resultados_iteracion_{iteracion}.csv")
        df_scores.to_csv(ruta_csv, index=False)

        print(f"🔹 Iteración {iteracion}: score final = {score_final:.4f}")
        print(f"📁 Detalle guardado en: {ruta_csv}")

        return float(score_final)

    except Exception as e:
        print(f"❌ Error al evaluar heurística: {e}")
        return 0.0


# ============================================================
# 3️⃣ Evaluar con timeout (para Windows)
# ============================================================
def evaluar_con_timeout(code, df, iteracion, carpeta, timeout_sec=120):
    """Ejecuta evaluate_candidate con límite de tiempo."""
    result = [0.0]

    def _run():
        result[0] = evaluate_candidate(code, df, iteracion, carpeta)

    thread = threading.Thread(target=_run)
    thread.start()
    thread.join(timeout_sec)

    if thread.is_alive():
        print(f"⚠️ Iteración {iteracion}: tiempo excedido (> {timeout_sec}s). Se omite.")
        return 0.0
    return result[0]


# ============================================================
# 4️⃣ Diagnóstico gráfico al finalizar
# ============================================================
def diagnostico_funsearch(csv_path="resultados_funsearch.csv"):
    if not os.path.exists(csv_path):
        print("⚠️ No se encontró el archivo de resultados.")
        return
    df = pd.read_csv(csv_path)
    df_ok = df[df["estado"] == "OK"]

    plt.figure(figsize=(8, 4))
    plt.plot(df_ok["iteracion"], df_ok["score_final"], marker="o")
    plt.xlabel("Iteración")
    plt.ylabel("Score normalizado")
    plt.title("Evolución del score durante FunSearch")
    plt.grid(True)
    plt.show()

    print("\n📊 Diagnóstico:")
    print(f"Iteraciones totales: {len(df)}")
    print(f"Mejor score: {df_ok['score_final'].max():.4f}")
    print(f"Promedio: {df_ok['score_final'].mean():.4f}")
    print(f"Tasa de éxito: {len(df_ok) / len(df) * 100:.2f}%")


# ============================================================
# 5️⃣ Bucle principal con prompt original + evolución + timeout
# ============================================================
def main():
    ruta_base = r"salida_muestras\lotes_100_df.pkl"
    carpeta_heuristicas = "salida_heuristicas"
    archivo_resultados = "resultados_funsearch.csv"
    os.makedirs(carpeta_heuristicas, exist_ok=True)

    df_recuperado = cargar_base_pickle(ruta_base)
    print(df_recuperado.head())

    API_KEY = "#colocar su clave de api de gemini#"
    MODEL = "gemini-2.5-flash"
    N_ITER = 200

    # ============================================================
    # Inicializar historial de mejores heurísticas (memoria evolutiva)
    # ============================================================
    historial_texto = ""


    with open("my_greedy_heuristic.py", "r", encoding="utf-8") as f:
        base_code = f.read()

    mejor_score = 0.0
    mejor_code = base_code
    resultados = []

    for i in range(1, N_ITER + 1):
        print(f"\n=== 🔁 Iteración {i} ===")
        TEMPERATURE = TEMPERATURE = random.randint(3, 9)/10
        gemini = Gemini(api_key=API_KEY, model_name=MODEL, temperature=TEMPERATURE)

        # ============================================================
        # Construcción del prompt (versión original + historial)
        # ============================================================
        df_tmp = pd.DataFrame(resultados)

        if (
                len(df_tmp) > 0
                and "estado" in df_tmp.columns
                and "score_final" in df_tmp.columns
                and "archivo" in df_tmp.columns
        ):
            df_ok = df_tmp[df_tmp["estado"] == "OK"]
            if not df_ok.empty:
                mejores_iteraciones = df_ok.nlargest(5, "score_final")[["archivo", "score_final"]]
            else:
                mejores_iteraciones = pd.DataFrame(columns=["archivo", "score_final"])
        else:
            mejores_iteraciones = pd.DataFrame(columns=["archivo", "score_final"])

        prompt = f"""
        ### OBJECTIVE:
        Improve the internal logic, focusing on classic KP strategies (e.g., greedy approach based on value/weight ratio, fractional relaxation, dynamic programming concepts, or better pruning/bounding) to increase the resulting value, improve knapsack filling, or reduce execution time compared to the current score: {mejor_score:.4f}
        
        ###  CORE RULES (MUST BE FOLLOWED):
        1.  **Syntactic Integrity:** The generated code MUST be 100% syntactically valid and MUST successfully pass Python's `ast.parse()` check.
        2.  **Bracket Balance:** All parentheses `()`, square brackets `[]`, and curly braces `{{}}` MUST be **perfectly balanced**.
        3.  **Python Indentation:** Indentation MUST be consistent and use **4 spaces** per level. Incorrect indentation will be treated as an error.
        4.  **Self-Contained Function:** The function body MUST be entirely self-contained. **DO NOT** include any external `import` statements (e.g., `import math`, `import random`) inside the function. Assume the environment provides basic functions, or use built-in types only.
        5.  **Triple Quotes Forbidden:** Use **only** single-line comments (`#`). **DO NOT** use triple quotes (`'''` or `\"\"\"`) anywhere in the code.
        6.  **Function Signature:** The function signature MUST begin **EXACTLY** with: `def heuristic(items_state):`
        7.  **Required Output:** The function MUST explicitly return a numerical value (float or int) representing the calculated value/score.
        
        {{CODE_TO_IMPROVE}}
        {historial_texto if historial_texto else mejor_code}
        {{/CODE_TO_IMPROVE}}
        
        ### REQUIRED_FINAL_FUNCTION:
        def heuristic(items_state):
         
        the function will have at the end os script=   return 
        "items": list(current_selected_items_indices),
        "total_value": current_total_value,
        "total_peso_usado": current_total_weight,
        "solve_time": end_time - start_time
        """

        try:
            # ============================================================
            # 🧩 1. Generar el código con Gemini
            # ============================================================
            raw_output = gemini.predict(prompt)[0]

            # ============================================================
            # 🧹 2. Limpieza del código generado
            # ============================================================
            # Elimina etiquetas residuales
            raw_output = raw_output.replace(")] role='model'", "")
            raw_output = raw_output.replace('")] role=\'model\'', "")

            # Limpieza general de caracteres extraños
            new_code = raw_output.strip()
            new_code = re.sub(r"^```[a-zA-Z]*|```$", "", new_code)  # elimina ```python
            new_code = new_code.replace('\t', '    ')  # convierte tabs a espacios
            new_code = new_code.replace('"""', '# ').replace("'''", '# ')  # elimina docstrings
            new_code = new_code.replace('#"', '').replace('#”', '').replace('”', '').replace('“', '').strip()
            new_code = new_code.replace('‘', '').replace('’', '')  # comillas curvas
            new_code = new_code.replace('`', '')  # backticks
            new_code = new_code.replace("\\", "")  # barras invertidas aisladas

            # Busca el inicio de la función esperada
            inicio = new_code.find("def heuristic(items_state):")
            if inicio == -1:
                raise ValueError("No se encontró 'def heuristic(items_state):'")
            new_code = new_code[inicio:].strip()

            # ============================================================
            # 🧪 3. Validación de sintaxis
            # ============================================================
            try:
                compile(new_code, "<string>", "exec")  # más claro que ast.parse()
            except SyntaxError as e:
                print("\n⚠️ Código con sintaxis inválida en iteración", i)
                print("Detalles:", e)
                print("\n=== Código problemático ===\n")
                print(new_code)
                print("\n=== Fin del código ===\n")
                resultados.append({"iteracion": i, "score_final": 0.0, "estado": "ErrorSintaxis"})
                continue

            # ============================================================
            # ✅ 4. Si pasa la validación, se continúa con el resto del ciclo
            # ============================================================
            # (aquí se evalúa la heurística, se calcula el score, etc.)

        except Exception as e:
            print(f"⚠️ Error en generación: {e}")
            resultados.append({"iteracion": i, "score_final": 0.0, "estado": "Error"})
            continue


        # ============================================================
        # Evaluar heurística con timeout (máx. 3 minutos)
        # ============================================================
        score = evaluar_con_timeout(new_code, df_recuperado, i, carpeta_heuristicas)

        archivo_heuristica = f"heuristica_iter{i}.py"
        ruta = os.path.join(carpeta_heuristicas, archivo_heuristica)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(new_code)

        resultados.append({
            "iteracion": i,
            "score_final": score,
            "archivo": archivo_heuristica,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado": "OK" if score > 0 else "Error"
        })
        pd.DataFrame(resultados).to_csv(archivo_resultados, index=False)

        # ============================================================
        # Actualizar historial con las mejores heurísticas recientes
        # ============================================================
        df_tmp = pd.DataFrame(resultados)
        df_ok = df_tmp[df_tmp["estado"] == "OK"]
        if not df_ok.empty:
            top5 = df_ok.nlargest(5, "score_final")
            historial_texto = "\n\n".join(
                [open(os.path.join(carpeta_heuristicas, r["archivo"]), encoding="utf-8").read()
                 for _, r in top5.iterrows()]
            )

        if score > mejor_score:
            mejor_score, mejor_code = score, new_code
            print(f"✅ Nueva mejor heurística: score = {mejor_score:.6f}")

    # ============================================================
    # Finalizar búsqueda y diagnóstico
    # ============================================================
    with open("best_candidate_code.py", "w", encoding="utf-8") as f:
        f.write(mejor_code)
    print(f"\n🏁 Búsqueda terminada. Mejor score: {mejor_score:.6f}")
    print("💾 Mejor código guardado en: best_candidate_code.py")

    diagnostico_funsearch(archivo_resultados)


# ============================================================
if __name__ == "__main__":
    main()
