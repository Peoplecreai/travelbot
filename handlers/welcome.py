import re
import datetime
from config import db

def handle_welcome(text, say, state, doc_ref, user_id):
    now_ts = datetime.datetime.utcnow().timestamp()
    # Detectar saludo típico al inicio
    if re.search(r'\b(hola|buen[oa]s?|hey|hi)\b', text, re.IGNORECASE):
        profile_ref = db.collection("profiles").document(user_id)
        profile = profile_ref.get().to_dict() or {}
        last_dest = profile.get("last_destination")
        if last_dest:
            say(f"¡Hola! 👋 ¿Cómo te fue en {last_dest}? ¿En qué puedo ayudarte hoy?")
        else:
            say("¡Hola! 👋 Soy TravelBot, ¿en qué puedo ayudarte con tu viaje?")
        state['last_ts'] = now_ts
        doc_ref.set(state)
        return True
    return False
