from fastapi import Request, Response
from itsdangerous import URLSafeSerializer, BadSignature
from app.config import settings
import time

class SessionManager:
    """
    Gestor de sesiones para el sistema de quiz.
    
    Esta clase maneja la creación, lectura, escritura y validación de sesiones
    de usuario utilizando cookies firmadas para mantener el estado del quiz
    de forma segura entre requests.
    
    La sesión almacena:
    - Puntaje actual del usuario
    - Total de preguntas respondidas
    - Tiempo de inicio del quiz
    - Pregunta actual
    - Lista de errores cometidos
    """
    
    def __init__(self):
        """
        Inicializa el gestor de sesiones con el serializador seguro.
        
        Utiliza la clave secreta de configuración para firmar las cookies
        y prevenir manipulación por parte del cliente.
        """
        self.serializer = URLSafeSerializer(settings.SESSION_SECRET_KEY)
    
    def get_session(self, request: Request) -> dict:
        """
        Obtiene los datos de sesión desde la cookie del request.
        
        Args:
            request (Request): El objeto request de FastAPI
            
        Returns:
            dict: Datos de sesión deserializados, o diccionario vacío si no existe
                 o la cookie está corrupta
        """
        cookie = request.cookies.get(settings.SESSION_COOKIE)
        if not cookie:
            return {}
        
        try:
            return self.serializer.loads(cookie)
        except BadSignature:
            return {}
    
    def set_session(self, response: Response, session_data: dict) -> None:
        """
        Establece los datos de sesión en una cookie firmada.
        
        Args:
            response (Response): El objeto response de FastAPI
            session_data (dict): Datos de sesión a serializar y almacenar
        """
        cookie_value = self.serializer.dumps(session_data)
        response.set_cookie(
            settings.SESSION_COOKIE, 
            cookie_value, 
            httponly=True, 
            max_age=settings.SESSION_MAX_AGE
        )
    
    def clear_session(self, response: Response) -> None:
        """
        Elimina la cookie de sesión del cliente.
        
        Args:
            response (Response): El objeto response de FastAPI
        """
        response.delete_cookie(settings.SESSION_COOKIE)
    
    def create_new_session(self, initial_question: dict) -> dict:
        """
        Crea una nueva sesión de quiz con valores iniciales.
        
        Args:
            initial_question (dict): Primera pregunta del quiz
            
        Returns:
            dict: Nueva sesión inicializada con valores por defecto
        """
        return {
            'puntaje': 0,
            'total': 0,
            'inicio': int(time.time()),
            'pregunta_actual': initial_question,
            'errores': []
        }
    
    def is_session_valid(self, session: dict) -> bool:
        """
        Valida que una sesión contenga todos los campos requeridos.
        
        Args:
            session (dict): Datos de sesión a validar
            
        Returns:
            bool: True si la sesión es válida, False en caso contrario
        """
        required_fields = ['puntaje', 'total', 'inicio', 'pregunta_actual']
        return all(field in session for field in required_fields) and session != {}

session_manager = SessionManager()
