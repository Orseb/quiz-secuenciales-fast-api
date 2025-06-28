def is_question_valid(question: dict) -> bool:
    """
    Valida que una pregunta tenga la estructura correcta y todos los campos requeridos.
    
    Verifica que la pregunta sea un diccionario válido, no contenga errores,
    tenga todos los campos obligatorios y que las respuestas sean una lista de 4 opciones.
    
    Args:
        question (dict): Diccionario con los datos de la pregunta a validar
        
    Returns:
        bool: True si la pregunta es válida, False en caso contrario
        
    Campos requeridos:
        - pregunta: Texto de la pregunta
        - codigo: Código Python a analizar
        - respuestas: Lista con exactamente 4 opciones
        - respuesta_correcta: La respuesta correcta
    """
    if not isinstance(question, dict):
        return False
    
    if 'error' in question:
        return False
    
    required_fields = ['pregunta', 'codigo', 'respuestas', 'respuesta_correcta']
    for field in required_fields:
        if field not in question or not question[field]:
            return False
    
    if not isinstance(question['respuestas'], list) or len(question['respuestas']) != 4:
        return False
    
    return True

def validate_question_structure(question_json: dict) -> dict:
    """
    Normaliza y valida la estructura de una pregunta desde JSON.
    
    Convierte el formato JSON recibido de la API a la estructura interna
    esperada por la aplicación. Maneja diferentes formatos de respuestas
    (string separado por comas o lista).
    
    Args:
        question_json (dict): Pregunta en formato JSON crudo de la API
        
    Returns:
        dict: Pregunta normalizada con la estructura estándar
        
    Transformaciones realizadas:
        - Convierte "Respuestas" string a lista si es necesario
        - Mapea campos del JSON a nombres internos
        - Agrega campos opcionales con valores por defecto
    """
    respuestas = question_json.get("Respuestas")
    if isinstance(respuestas, str):
        respuestas = [r.strip() for r in respuestas.split(",")]
    elif not isinstance(respuestas, list):
        respuestas = []
    
    question = {
        "pregunta": question_json.get("Pregunta"),
        "codigo": question_json.get("Codigo"),
        "respuestas": respuestas,
        "respuesta_correcta": question_json.get("Respuesta correcta"),
        "explicacion": question_json.get("Explicacion", ""),
        "tematicas_usadas": question_json.get("tematicas_usadas", [])
    }
    
    return question
