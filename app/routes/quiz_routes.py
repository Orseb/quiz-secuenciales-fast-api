import asyncio
from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.utils import session_manager, is_question_valid
from app.services import cache_manager
import time
import os

router = APIRouter()
templates_path = os.path.join(os.path.dirname(__file__), '..', '..', settings.TEMPLATES_DIR)
templates = Jinja2Templates(directory=templates_path)

@router.get('/', name="inicio")
def inicio(request: Request):
    """
    Ruta de inicio de la aplicación.
    
    Muestra la página principal del quiz y limpia cualquier sesión existente
    para permitir que el usuario comience un nuevo quiz desde cero.
    
    Args:
        request (Request): Objeto request de FastAPI
        
    Returns:
        TemplateResponse: Página HTML de inicio con información del quiz
    """
    response = templates.TemplateResponse('inicio.html', {'request': request})
    session_manager.clear_session(response)
    return response

@router.get("/quiz", name="quiz")
async def quiz_get(request: Request):
    """
    Muestra la pregunta actual del quiz.
    
    Esta ruta maneja la lógica principal del quiz:
    - Valida o crea una nueva sesión
    - Obtiene una pregunta válida del cache
    - Maneja reintentos en caso de preguntas inválidas
    - Actualiza la sesión con la pregunta actual
    
    Args:
        request (Request): Objeto request de FastAPI
        
    Returns:
        TemplateResponse: Página HTML con la pregunta actual
        RedirectResponse: Redirección a error si no se puede generar pregunta válida
    """
    session = session_manager.get_session(request)

    if not session_manager.is_session_valid(session):
        new_question = await cache_manager.get_question_from_cache_async()
        attempts = 0
        
        while not is_question_valid(new_question) and attempts < 10:
            await asyncio.sleep(2)
            new_question = await cache_manager.get_question_from_cache_async()
            attempts += 1
        
        if not is_question_valid(new_question):
            return RedirectResponse(
                url=f'/error?detalle=Límite%20de%20intentos%20superado&texto=No%20se%20pudo%20generar%20una%20pregunta%20válida.%20Por%20favor%20intente%20nuevamente%20más%20tarde.',
                status_code=303
            )
        
        session = session_manager.create_new_session(new_question)

    attempts = 0
    while not is_question_valid(session['pregunta_actual']) and attempts < 10:
        await asyncio.sleep(2)
        session['pregunta_actual'] = await cache_manager.get_question_from_cache_async()
        attempts += 1
    
    if not is_question_valid(session['pregunta_actual']):
        return RedirectResponse(
            url=f'/error?detalle=Límite%20de%20intentos%20superado&texto=No%20se%20pudo%20generar%20una%20pregunta%20válida.%20Por%20favor%20intente%20nuevamente%20más%20tarde.',
            status_code=303
        )

    question = session['pregunta_actual']
    question_number = session.get('total', 0) + 1
    
    response = templates.TemplateResponse(
        'quiz.html',
        {'request': request, 'pregunta': question, 'num_pregunta': question_number}
    )
    
    session_manager.set_session(response, session)
    return response

@router.post('/quiz')
async def quiz_post(request: Request, respuesta: str = Form(...)):
    """
    Procesa la respuesta del usuario y avanza al siguiente estado del quiz.
    
    Funcionalidades:
    - Valida la sesión actual
    - Compara la respuesta del usuario con la correcta
    - Actualiza el puntaje si es correcta
    - Redirige al resultado si se completaron todas las preguntas
    - Obtiene la siguiente pregunta y actualiza la sesión
    
    Args:
        request (Request): Objeto request de FastAPI
        respuesta (str): Respuesta seleccionada por el usuario
        
    Returns:
        RedirectResponse: Redirección a la siguiente pregunta, resultado o error
    """
    session = session_manager.get_session(request)
    
    if not session_manager.is_session_valid(session):
        return RedirectResponse(url='/', status_code=303)

    attempts = 0
    while not is_question_valid(session['pregunta_actual']) and attempts < 10:
        await asyncio.sleep(2)
        session['pregunta_actual'] = await cache_manager.get_question_from_cache_async()
        attempts += 1
    
    if not is_question_valid(session['pregunta_actual']):
        return RedirectResponse(
            url=f'/error?detalle=Límite%20de%20intentos%20superado&texto=No%20se%20pudo%20generar%20una%20pregunta%20válida.%20Por%20favor%20intente%20nuevamente%20más%20tarde.',
            status_code=303
        )

    selection = respuesta
    correct_answer = session['pregunta_actual']['respuesta_correcta']
    session['total'] += 1

    if selection and selection.strip() == correct_answer.strip():
        session['puntaje'] += 1

    if session['total'] >= settings.TOTAL_QUESTIONS:
        elapsed_time = int(time.time() - session['inicio'])
        score = session['puntaje']
        
        response = RedirectResponse(
            url=f'/resultado?correctas={score}&tiempo={elapsed_time}',
            status_code=303
        )
        session_manager.clear_session(response)
        return response

    new_question = await cache_manager.get_question_from_cache_async()
    attempts = 0
    
    while not is_question_valid(new_question) and attempts < 10:
        await asyncio.sleep(2)
        new_question = await cache_manager.get_question_from_cache_async()
        attempts += 1
    
    if not is_question_valid(new_question):
        return RedirectResponse(
            url=f'/error?detalle=Límite%20de%20intentos%20superado&texto=No%20se%20pudo%20generar%20una%20pregunta%20válida.%20Por%20favor%20intente%20nuevamente%20más%20tarde.',
            status_code=303
        )
    
    session['pregunta_actual'] = new_question
    response = RedirectResponse(url='/quiz', status_code=303)
    session_manager.set_session(response, session)
    return response

@router.get('/resultado')
def resultado(request: Request, correctas: int = 0, tiempo: int = 0):
    """
    Muestra los resultados finales del quiz.
    
    Presenta al usuario su puntaje final, tiempo transcurrido y opcionalmente
    las preguntas que respondió incorrectamente con sus explicaciones.
    
    Args:
        request (Request): Objeto request de FastAPI
        correctas (int): Número de respuestas correctas
        tiempo (int): Tiempo total en segundos
        
    Returns:
        TemplateResponse: Página HTML con los resultados del quiz
    """
    response = templates.TemplateResponse(
        'resultado.html',
        {
            'request': request, 
            'correctas': correctas, 
            'tiempo': tiempo, 
            'errores': []
        }
    )
    return response

@router.get('/error')
def error(request: Request, detalle: str = '', texto: str = ''):
    """
    Muestra página de error cuando ocurre un problema en la generación de preguntas.
    
    Args:
        request (Request): Objeto request de FastAPI
        detalle (str): Descripción del error ocurrido
        texto (str): Texto adicional o respuesta de la API que causó el error
        
    Returns:
        TemplateResponse: Página HTML de error con código de estado 500
    """
    return templates.TemplateResponse(
        'error.html',
        {'request': request, 'detalle': detalle, 'texto': texto},
        status_code=500
    )
