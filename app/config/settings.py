import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Configuración principal de la aplicación Quiz de Python.
    
    Esta clase centraliza todas las variables de configuración necesarias
    para el funcionamiento de la aplicación, incluyendo claves de API,
    configuración de sesiones y parámetros del cache.
    
    Attributes:
        GENAI_API_KEY (str): Clave de API para Google Gemini AI
        SESSION_SECRET_KEY (str): Clave secreta para firmar cookies de sesión
        CACHE_SIZE (int): Tamaño máximo del cache de preguntas
        CACHE_MIN (int): Número mínimo de preguntas en cache antes de recargar
        TOTAL_QUESTIONS (int): Total de preguntas por quiz
        SESSION_COOKIE (str): Nombre de la cookie de sesión
        SESSION_MAX_AGE (int): Tiempo de vida de la sesión en segundos
        TEMPLATES_DIR (str): Directorio donde se encuentran las plantillas HTML
    """
    GENAI_API_KEY: str = os.getenv("GENAI_API_KEY")
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY")
    
    # Configuración del cache de preguntas
    CACHE_SIZE: int = 200  # Máximo de preguntas en cache
    CACHE_MIN: int = 100   # Mínimo antes de recargar
    
    # Configuración del quiz
    TOTAL_QUESTIONS: int = 10  # Total de preguntas por sesión
    
    # Configuración de sesiones
    SESSION_COOKIE: str = "quiz_session"
    SESSION_MAX_AGE: int = 60 * 60 * 60  # 1 hora en segundos
    
    # Configuración de plantillas
    TEMPLATES_DIR: str = "templates"
    
    def __init__(self):
        """
        Inicializa la configuración y valida que las variables críticas estén presentes.
        
        Raises:
            RuntimeError: Si GENAI_API_KEY o SESSION_SECRET_KEY no están configuradas
        """
        if not self.GENAI_API_KEY:
            raise RuntimeError("GENAI_API_KEY not found in environment variables")
        
        if not self.SESSION_SECRET_KEY:
            raise RuntimeError(
                "SESSION_SECRET_KEY is not configured. "
                "Set a secure value in your environment or .env file."
            )

settings = Settings()
