import queue
import threading
import time
import asyncio
from app.config import settings
from app.services.gemini_service import gemini_service
from app.utils.question_validator import is_question_valid

class CacheManager:
    """
    Gestor de cache de preguntas para optimizar el rendimiento del quiz.
    
    Esta clase mantiene un cache en memoria de preguntas pre-generadas para
    reducir la latencia y mejorar la experiencia del usuario. Utiliza un hilo
    en segundo plano para mantener el cache lleno y gestiona las temáticas
    previas para evitar repeticiones.
    
    Características:
    - Cache thread-safe con queue.Queue
    - Precarga automática en segundo plano
    - Gestión de temáticas previas para variedad
    - Manejo de errores y límites de API
    
    Attributes:
        question_cache (Queue): Cola thread-safe para almacenar preguntas
        previous_topics_global (list): Lista global de temáticas usadas
        topics_lock (threading.Lock): Lock para acceso thread-safe a temáticas
    """
    
    def __init__(self):
        """
        Inicializa el gestor de cache y arranca el hilo de precarga.
        
        Configura la cola de preguntas con el tamaño máximo definido en settings
        e inicia el hilo daemon que se encarga de mantener el cache lleno.
        """
        self.question_cache = queue.Queue(maxsize=settings.CACHE_SIZE)
        self.previous_topics_global = []
        self.topics_lock = threading.Lock()
        self._start_preload_thread()
    
    def _start_preload_thread(self):
        """
        Inicia el hilo daemon para precarga de preguntas en segundo plano.
        
        El hilo daemon se ejecuta continuamente y se encarga de mantener
        el cache con suficientes preguntas válidas para servir requests.
        """
        preload_thread = threading.Thread(target=self._preload_questions, daemon=True)
        preload_thread.start()
    
    def _preload_questions(self):
        """
        Bucle principal del hilo de precarga de preguntas.
        
        Este método se ejecuta continuamente en segundo plano:
        - Verifica si el cache necesita más preguntas
        - Genera nuevas preguntas usando el servicio Gemini
        - Maneja errores de API y límites de rate
        - Actualiza las temáticas globales para evitar repeticiones
        
        Manejo de errores:
        - RESOURCE_EXHAUSTED: Espera 35 segundos (límite de API)
        - Otros errores: Espera 5 segundos antes de reintentar
        """
        while True:
            if self.question_cache.qsize() < settings.CACHE_MIN:
                try:
                    with self.topics_lock:
                        previous_topics = list(self.previous_topics_global)
                    
                    question = gemini_service.generate_question(previous_topics)
                    
                    if is_question_valid(question):
                        self.question_cache.put(question)
                        
                        with self.topics_lock:
                            self.previous_topics_global.extend(question.get("tematicas_usadas", [])) #Se agregan las nuevas temáticas a la lista
                            if len(self.previous_topics_global) > settings.MAX_PREVIOUS_TOPICS:
                                self.previous_topics_global = [] #Se asegura que no se acumulen demasiadas temáticas previas
                    
                    time.sleep(5)
                    
                except Exception as e:
                    if "RESOURCE_EXHAUSTED" in str(e):
                        time.sleep(35)
                    else:
                        time.sleep(5)
            else:
                time.sleep(2)
    
    async def get_question_from_cache_async(self, previous_topics: list = None) -> dict:
        """
        Obtiene una pregunta del cache de forma asíncrona.
        
        Intenta obtener una pregunta pre-generada del cache. Si no hay preguntas
        disponibles o la pregunta no es válida, genera una nueva directamente.
        
        Args:
            previous_topics (list, optional): Temáticas previas para evitar repetición
            
        Returns:
            dict: Pregunta válida lista para usar en el quiz
            
        Nota:
            Utiliza run_in_executor para hacer thread-safe la operación de queue
            en el contexto asíncrono de FastAPI.
        """
        loop = asyncio.get_running_loop()
        
        try:
            question = await loop.run_in_executor(
                None, 
                lambda: self.question_cache.get(timeout=10)
            )
            
            if not is_question_valid(question):
                return gemini_service.generate_question(previous_topics)
            
            return question
            
        except Exception:
            question = gemini_service.generate_question(previous_topics)
            return question
    
    def get_cache_size(self) -> int:
        """
        Obtiene el número actual de preguntas en cache.
        
        Returns:
            int: Cantidad de preguntas disponibles en el cache
        """
        return self.question_cache.qsize()
    
    def clear_cache(self):
        """
        Vacía completamente el cache de preguntas.
        
        Útil para reiniciar el sistema o limpiar preguntas inválidas.
        Remueve todas las preguntas del cache de forma thread-safe.
        """
        while not self.question_cache.empty():
            try:
                self.question_cache.get_nowait()
            except queue.Empty:
                break

cache_manager = CacheManager()
