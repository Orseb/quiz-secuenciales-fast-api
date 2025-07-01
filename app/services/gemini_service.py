import json
from google import genai
from app.config import settings
from app.prompts import build_prompt_with_previous_topics
from app.utils.question_validator import is_question_valid, validate_question_structure

class GeminiService:
    """
    Servicio para interactuar con la API de Google Gemini AI.
    
    Esta clase encapsula toda la lógica de comunicación con Gemini para
    generar preguntas de quiz de Python. Maneja la construcción de prompts,
    el procesamiento de respuestas y la validación de preguntas generadas.
    
    Utiliza el modelo gemini-2.5-flash-lite-preview-06-17 optimizado para
    generación rápida de contenido estructurado.
    
    Attributes:
        client: Cliente de Google Gemini AI
        model_name (str): Nombre del modelo de IA utilizado
    """
    
    def __init__(self):
        """
        Inicializa el servicio Gemini con la configuración de API.
        
        Configura el cliente usando la clave de API desde settings y
        establece el modelo específico para generación de preguntas.
        """
        self.client = genai.Client(api_key=settings.GENAI_API_KEY)
        self.model_name = "gemini-2.5-flash-lite-preview-06-17"
    
    def generate_question(self, previous_topics: list = None) -> dict:
        """
        Genera una nueva pregunta de quiz usando Gemini AI.
        
        Construye un prompt personalizado con las temáticas previas para evitar
        repeticiones, envía la solicitud a Gemini y procesa la respuesta para
        obtener una pregunta estructurada.
        
        Args:
            previous_topics (list, optional): Lista de temáticas usadas previamente
                                            para evitar repetición en la nueva pregunta
            
        Returns:
            dict: Pregunta generada con estructura válida, o diccionario de error
                 si ocurre algún problema en la generación
                 
        Estructura de pregunta válida:
            {
                "pregunta": "Texto de la pregunta",
                "codigo": "Código Python a analizar", 
                "respuestas": ["Opción A", "Opción B", "Opción C", "Opción D"],
                "respuesta_correcta": "Respuesta correcta",
                "explicacion": "Explicación detallada",
                "tematicas_usadas": ["tema1", "tema2"]
            }
        """
        if previous_topics is None:
            previous_topics = []
        
        prompt = build_prompt_with_previous_topics(previous_topics)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            return self._process_response(response)
            
        except Exception as e:
            return {
                "error": "Failed to generate question",
                "detalle": str(e),
                "texto": "API call failed"
            }
    
    def _process_response(self, response) -> dict:
        """
        Procesa la respuesta cruda de Gemini y extrae la pregunta estructurada.
        
        Realiza las siguientes operaciones:
        1. Limpia el texto de respuesta (remueve delimitadores de código)
        2. Parsea el JSON de la respuesta
        3. Valida y normaliza la estructura de la pregunta
        4. Verifica que la pregunta sea válida según nuestros criterios
        
        Args:
            response: Respuesta cruda del modelo Gemini
            
        Returns:
            dict: Pregunta procesada y validada, o diccionario de error
                 si no se puede procesar correctamente
        """
        try:
            text = response.text.strip()
            
            text = self._clean_response_text(text)
            
            question_json = json.loads(text)
            
            question = validate_question_structure(question_json)
            
            if not is_question_valid(question):
                return {
                    "error": "Invalid or incomplete question",
                    "detalle": "Missing fields or incorrect format",
                    "texto": text
                }
            
            return question
            
        except json.JSONDecodeError as e:
            return {
                "error": "Could not extract JSON",
                "detalle": str(e),
                "texto": response.text
            }
        except Exception as e:
            return {
                "error": "Response processing failed",
                "detalle": str(e),
                "texto": response.text
            }
    
    def _clean_response_text(self, text: str) -> str:
        """
        Limpia el texto de respuesta removiendo delimitadores de código.

        Gemini a veces incluye delimitadores ```json o ``` en sus respuestas.
        Esta función los remueve para obtener JSON puro que se pueda parsear.
        
        Args:
            text (str): Texto crudo de respuesta de Gemini
            
        Returns:
            str: Texto limpio sin delimitadores, listo para parsear como JSON
        """

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()

gemini_service = GeminiService()
