import re
import datetime

def handle_welcome(text, say, state, doc_ref):
    now_ts = datetime.datetime.utcnow().timestamp()
    # Detectar saludo típico al inicio
    if re.search(r'\b(hola|buen[oa]s?|hey|hi)\b', text, re.IGNORECASE):
        say("¡Hola! 👋 Soy TravelBot, ¿en qué puedo ayudarte con tu viaje?")
        state['last_ts'] = now_ts
        doc_ref.set(state)
        return True
    return False
