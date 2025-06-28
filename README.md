# Documentación de la API

## Descripción General

La API del Quiz de Python proporciona endpoints para gestionar quizzes interactivos de análisis de código Python. Utiliza FastAPI como framework web y Google Gemini para la generación de preguntas.

## Base URL

```
http://localhost:8000
```

## Endpoints

### 1. Página de Inicio

**GET** `/`

Muestra la página de inicio de la aplicación y limpia cualquier sesión existente.

**Respuesta:**
- Renderiza la plantilla `inicio.html`
- Limpia cookies de sesión

**Ejemplo:**
```bash
curl -X GET http://localhost:8000/
```

---

### 2. Obtener Pregunta del Quiz

**GET** `/quiz`

Obtiene la pregunta actual del quiz. Si no existe una sesión válida, crea una nueva con la primera pregunta.

**Respuesta:**
- Renderiza la plantilla `quiz.html` con la pregunta actual
- Establece cookie de sesión

**Parámetros de respuesta:**
- `pregunta`: Objeto con la pregunta actual
- `num_pregunta`: Número de pregunta (1-10)

**Ejemplo:**
```bash
curl -X GET http://localhost:8000/quiz
```

---

### 3. Enviar Respuesta

**POST** `/quiz`

Procesa la respuesta del usuario y avanza al siguiente estado del quiz.

**Parámetros del cuerpo (form-data):**
- `respuesta` (string, requerido): La opción seleccionada por el usuario

**Respuestas posibles:**
- Redirección a `/quiz` para la siguiente pregunta
- Redirección a `/resultado` si se completaron las 10 preguntas
- Redirección a `/error` si hay problemas con la generación de preguntas

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "respuesta=Opción A"
```

---

### 4. Resultados del Quiz

**GET** `/resultado`

Muestra los resultados finales del quiz completado.

**Parámetros de consulta:**
- `correctas` (int): Número de respuestas correctas
- `tiempo` (int): Tiempo total en segundos

**Respuesta:**
- Renderiza la plantilla `resultado.html`
- Muestra puntuación y errores cometidos

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/resultado?correctas=7&tiempo=180"
```

---

### 5. Página de Error

**GET** `/error`

Muestra información detallada sobre errores ocurridos durante la generación de preguntas.

**Parámetros de consulta:**
- `detalle` (string): Descripción del error
- `texto` (string): Texto adicional del error

**Respuesta:**
- Renderiza la plantilla `error.html`
- Código de estado HTTP 500

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/error?detalle=Error%20de%20API&texto=Límite%20excedido"
```

## Gestión de Sesiones

La aplicación utiliza cookies firmadas para mantener el estado de la sesión:

### Estructura de la Sesión

```json
{
  "puntaje": 0,
  "total": 0,
  "inicio": 1640995200,
  "pregunta_actual": {
    "pregunta": "¿Cuál será la salida del siguiente código?",
    "codigo": "x = 5\ny = 3\nprint(x + y)",
    "respuestas": ["8", "53", "Error", "5 + 3"],
    "respuesta_correcta": "8",
    "explicacion": "Se suman los valores numéricos 5 + 3 = 8"
  },
  "errores": []
}
```

### Campos de la Sesión

- `puntaje`: Número de respuestas correctas
- `total`: Número total de preguntas respondidas
- `inicio`: Timestamp de inicio del quiz
- `pregunta_actual`: Objeto con la pregunta actu
