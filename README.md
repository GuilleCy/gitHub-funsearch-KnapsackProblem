# gitHub-funsearch-KnapsackProblem
El Knapsack Problem (KP) es un problema NP-Duro, por lo que diseñar heurísticas efectivas suele requerir experiencia, prueba y error.
FunSearch permite explorar automáticamente el espacio algorítmico mediante evolución de programas.
Este proyecto investiga si un marco híbrido FunSearch + IAG puede generar heurísticas competitivas sin intervención manual.

📁 Estructura del proyecto

Para revisar la implementación completa, debe ingresar a la carpeta nueva_ejecucion, donde se encuentra la aplicación de FunSearch en el problema de la mochila.

Dentro de esta carpeta se incluyen varios directorios:

1. Muestras guardadas

Contiene las muestras sintéticas generadas para replicar instancias del problema de la mochila.

2. resultados guardados

Incluye los archivos que almacenan la aplicación de las heurísticas y otros métodos utilizados en la experimentación.

3. salidas_heuristicas

Aquí se almacenan todas las heurísticas generadas durante el proceso evolutivo de FunSearch.

4. salida_muestra

Guarda las bases de datos con los resultados luego de aplicar las heurísticas sobre las muestras generadas.

📘 Notebooks de análisis

Los siguientes notebooks permiten explorar los análisis y resultados generados:

**Analisis_informacion.ipynb**
Presenta el análisis inicial de la simulación y la aplicación de las heurísticas Greedy y OrTools, evaluadas sobre una muestra de tamaño creciente.

**AplicaiconModelo Mll.ipynb**
Muestra la aplicación de las heurísticas resultantes generadas por FunSearch.

**MuestraHomogenea.ipynb**
Contiene la creación de 100 muestras de 400 objetos usadas para validar las heurísticas del proceso.

🐍 Programas principales en Python

Estos son los archivos clave del proyecto y su propósito:

**DataSetSintetico.py**
Genera las muestras sintéticas utilizadas para evaluar heurísticas.

**generadorMuestrasUniformes.py**
Crea muestras bajo un criterio uniforme para pruebas controladas.

**skeleton_knapsack.py**
Archivo donde se especifica la definición del problema de la mochila.

**my_greesy_heuristic.py**
Implementación de la heurística base tipo Greedy.

**best_candidate_code.py**
Contiene la heurística ganadora obtenida por FunSearch.

**funsearch-loop.py**
Núcleo del sistema: aquí se definen

los validadores de heurísticas,

el prompt empleado para Gemini,

y el generador del indicador que asegura que cada nueva heurística cumpla los requisitos establecidos.
