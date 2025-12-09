# gemini_cliente.py (Versión corregida para gemini-2.5-flash)
import os
from google import genai
from google.genai import types


class Gemini:
    """
    Cliente que usa el SDK oficial de Google (google-genai) y evita el error 'to_dict'.
    Compatible con modelos como 'gemini-2.5-flash'.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash", **config_kwargs):
        # 1. Configuramos la clave de API en el entorno
        os.environ["GEMINI_API_KEY"] = api_key

        # 2. Inicializamos el cliente
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

        # 3. Guardamos la configuración base
        self.base_config_kwargs = config_kwargs

        print(f"Initialized Gemini with model: {self.model_name}, Base Config Args: {self.base_config_kwargs}")

    def predict(self, question: str, **predict_kwargs):
        """
        Envía un prompt a Gemini y devuelve la respuesta como lista de strings.
        """
        try:
            final_config_kwargs = {**self.base_config_kwargs, **predict_kwargs}
            config_object = types.GenerateContentConfig(**final_config_kwargs)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=question,
                config=config_object
            )

            # Ajuste para evitar error con 'Content'
            if response is None:
                raise ValueError("La respuesta del modelo es None")

            if hasattr(response, "candidates") and len(response.candidates) > 0:
                text = str(response.candidates[0].content).strip()
            elif hasattr(response, "text") and response.text:
                text = str(response.text).strip()
            else:
                raise ValueError("No se pudo extraer texto de la respuesta del modelo")

            return [text]

        except Exception as e:
            print(f"Error al generar la respuesta: {e}")
            return [f"ERROR: {e}"]

    def sugerir_codigo(self, prompt: str, base_code: str = "", intentos: int = 3) -> str:
        full_prompt = (
            f"{prompt}\n\n"
            "A continuación tienes el código base a mejorar:\n"
            "```python\n"
            f"{base_code}\n"
            "```\n\n"
            "Devuelve SOLO el nuevo código en Python, sin explicaciones ni comentarios extra. "
            "El código debe contener obligatoriamente 'def heuristic'."
        )

        for intento in range(1, intentos + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.base_config_kwargs.get("temperature", 0.8),
                        max_output_tokens=2048,
                    ),
                )

                # Extraemos texto según la versión del SDK
                text = ""
                if hasattr(response, "candidates") and len(response.candidates) > 0:
                    text = response.candidates[0].content
                elif hasattr(response, "text") and response.text:
                    text = response.text
                else:
                    raise ValueError("No se pudo extraer texto del modelo")

                text = text.strip()

                # Limpiamos posibles backticks
                if text.startswith("```python"):
                    text = text.replace("```python", "").replace("```", "").strip()

                # Ahora hacemos el chequeo más flexible: ignorando espacios y mayúsculas
                if "def heuristic" not in text.replace(" ", "").lower():
                    raise ValueError("El código generado no contiene la función 'heuristic'.")

                print(f"✅ Código generado correctamente (intento {intento})")
                return text

            except Exception as e:
                print(f"⚠️ Error en intento {intento}: {e}")
                if intento == intentos:
                    print("❌ Falló después de varios intentos.")
                    return f"# ERROR: No se pudo generar código ({e})"
