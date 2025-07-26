import os
import google.generativeai as genai
import json

# Configura Gemini con tu API KEY (debe estar como variable de entorno o puedes setear aquí directamente)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Prompt persistente (pon tu prompt aquí)
GEMINI_PROMPT = """
Eres el asistente principal de solicitudes internas en Creai. Actualmente gestionas viajes, pero más adelante atenderás otras peticiones. Conversa de forma breve y profesional sin repetir información de manera innecesaria.

Debes extraer los siguientes datos esenciales del viaje conversando solo lo necesario:

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
Si conoces viajes o preferencias previas del usuario gracias al historial incluido en el prompt, puedes saludar haciendo referencia a ellos de manera natural.
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

def handle_extract_data(text, say, state, doc_ref, user_id):
    # Historial de conversación
    history = state.get("history", [])
    history.append({"role": "user", "content": text})

    # Arma el contexto para Gemini
    conversation = ""
    for h in history:
        if h["role"] == "user":
            conversation += f"Usuario: {h['content']}\n"
        else:
            conversation += f"Asistente: {h['content']}\n"

    prompt = GEMINI_PROMPT + conversation

    # Llama a Gemini
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    reply = response.text.strip()

    # Intenta parsear JSON
    json_start = reply.find("{")
    json_end = reply.rfind("}") + 1
    datos = None
    if json_start != -1 and json_end != -1:
        try:
            posible_json = reply[json_start:json_end]
            datos = json.loads(posible_json)
        except Exception:
            datos = None

    # Si el JSON está completo y válido, termina y regresa datos
    if datos and all(k in datos and datos[k] for k in ["origin", "destination", "start_date", "motive"]):
        state["data"] = datos
        state["history"] = history
        doc_ref.set(state)
        return datos

    # Si Gemini responde texto (pregunta), mándalo y sigue esperando respuesta
    say(reply)
    state["history"] = history
    doc_ref.set(state)
    return None
