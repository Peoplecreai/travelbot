# extract.py

import google.generativeai as genai
import os
import json

REQUIRED_FIELDS = [
    "origin",
    "destination",
    "start_date",
    "return_date",
    "motive",
    "venue"
]

USER_PROMPT = """
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

def make_prompt(history):
    prompt = USER_PROMPT
    for turn in history:
        who = "Usuario" if turn["role"] == "user" else "Bot"
        prompt += f"{who}: {turn['parts'][0]}\n"
    prompt += "\nResponde según las instrucciones."
    return prompt

def extract_trip_data(history):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = make_prompt(history)
    response = model.generate_content(prompt)
    output = response.text.strip()

    try:
        data = json.loads(output)
        # Valida que todas las claves estén y tengan valor (puede ser null para return_date y venue)
        if all(k in data for k in REQUIRED_FIELDS) and all(
            data[k] not in [None, "null", ""] or k in ["return_date", "venue"] for k in REQUIRED_FIELDS
        ):
            # Además, valida formato de fechas DD/MM/YYYY si quieres, aquí puedes meter regex si lo requieres
            return data, None
    except Exception:
        pass

    return None, output
