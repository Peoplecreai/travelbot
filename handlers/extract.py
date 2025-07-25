import os
import google.generativeai as genai
import json

# PROMPT PARA GEMINI
AI_PROMPT = """
Eres un asistente especializado en reservas de viajes de negocio, amigable y profesional. Tu objetivo es guiar la conversación de manera natural y fluida para recopilar información del usuario sin ser invasivo.

Tu tarea principal es extraer los siguientes datos esenciales, preguntando solo lo necesario y de forma conversacional:

Origen: Ciudad de salida (por ejemplo, "Madrid" o "Nueva York").
Destino: Ciudad o lugar de llegada.
Fecha de salida: Parsea cualquier formato de fecha que proporcione el usuario (ejemplos: "25 de julio", "julio 25", "7/25", "mañana", etc.). Asume el año actual (2025) si no se especifica. Convierte internamente a formato YYYY-MM-DD para el JSON.
Fecha de regreso: Similar al anterior; si es un viaje de ida solo o no aplica, usa "null".
Motivo del viaje: Breve descripción (por ejemplo, "reunión con clientes" o "conferencia anual").
Venue: Nombre del evento, conferencia o lugar específico (si aplica; si no hay, usa "null").
Reglas estrictas:

NO preguntes ni asumas el nivel jerárquico del usuario, su rol en la empresa ni información personal innecesaria.
Si falta algún dato, pregunta SOLO por ese dato específico con una pregunta corta y natural (ejemplo: "¿Cuál es la ciudad de origen?").
Si detectas ambigüedad (como fechas vagas, destinos múltiples o formatos no estándar), pregunta para aclarar de inmediato sin asumir (ejemplo: "¿Te refieres a París en Francia o París en Texas?" o "¿La fecha de salida es el 25 de julio de este año?").
Parsea fechas de manera flexible y humana: interpreta expresiones como "el próximo lunes", "en dos semanas" o formatos informales basándote en la fecha actual (25 de julio de 2025). Si es ambiguo, aclara.
Mantén la conversación corta y enfocada; no agregues chit-chat innecesario a menos que el usuario lo inicie.
Si el usuario proporciona datos extra o corrige información, actualiza internamente y confirma sutilmente.
Una vez que tengas TODOS los datos completos y sin ambigüedades, termina la conversación respondiendo SOLO con un JSON válido en este formato exacto (sin explicaciones, sin texto adicional):
{
"origin": "...",
"destination": "...",
"start_date": "...",
"return_date": "...",
"motive": "...",
"venue": "..."
}

Si el JSON no está completo, continúa preguntando. Asegúrate de que las fechas en el JSON estén en formato DD/MM/YYYY y que el JSON sea parseable.

A continuación, la conversación previa:

"""

# Inicializa Gemini solo una vez
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

REQUIRED_FIELDS = ["origin", "destination", "start_date", "return_date", "motive", "venue"]

def extract_trip_data(conversation_history):
    """
    Llama a Gemini para extraer datos del viaje a partir de la conversación.
    Args:
        conversation_history (str): Conversación previa con el usuario.
    Returns:
        dict: Con los campos origin, destination, start_date, return_date, motive, venue.
    """
    prompt = AI_PROMPT + conversation_history
    response = model.generate_content(prompt)
    # Intenta extraer JSON de la respuesta
    try:
        json_start = response.text.find("{")
        json_end = response.text.rfind("}") + 1
        output = json.loads(response.text[json_start:json_end])
        return output
    except Exception:
        return None

def handle_extract_data(text, say, state, doc_ref, user_id):
    """
    Función que maneja la extracción y conversación para obtener datos del viaje.
    """
    conversation = state.get("conversation", "")
    conversation += f"Usuario: {text}\n"
    datos = extract_trip_data(conversation)

    # Si Gemini regresa JSON válido y completo, avanza
    if datos and all(k in datos and datos[k] not in [None, "null", ""] for k in REQUIRED_FIELDS):
        state["data"] = datos
        state["conversation"] = ""  # Limpia historial porque ya terminó
        doc_ref.set(state)
        return datos

    # Si no, sigue preguntando
    else:
        state["conversation"] = conversation
        doc_ref.set(state)
        # Si Gemini preguntó algo (no regresó JSON), mándalo al usuario
        # Asumimos que si no hay JSON, la respuesta de Gemini es una pregunta
        if datos is None:
            # Muestra la respuesta de Gemini tal cual (pregunta conversacional)
            respuesta = model.generate_content(AI_PROMPT + conversation).text
            say(respuesta.strip())
        else:
            # Pregunta por campos faltantes (fallback)
            faltantes = [k for k in REQUIRED_FIELDS if not datos.get(k)]
            if faltantes:
                preguntas = {
                    "origin": "¿De qué ciudad sales?",
                    "destination": "¿A qué ciudad viajas?",
                    "start_date": "¿Cuál es la fecha de salida?",
                    "return_date": "¿Y la de regreso? Si solo es ida, dime 'solo ida'.",
                    "motive": "¿Cuál es el motivo del viaje? (reunión, evento, capacitación, etc.)",
                    "venue": "¿Dónde se llevará a cabo el evento o visita? Dame el nombre del lugar o evento."
                }
                for k in faltantes:
                    say(preguntas[k])
                    break
        return None
