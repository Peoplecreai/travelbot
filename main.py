import os
import json
import functions_framework
from slack_bolt import App
from slack_bolt.adapter.google_cloud_functions import SlackRequestHandler
from google.cloud import firestore

from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, db
from handlers.welcome import handle_welcome
from handlers.extract import handle_extract_data
from handlers.search import handle_search_and_buttons
from handlers.actions import register_actions
from handlers.summary import handle_summary
from utils.timeouts import reset_state_if_timeout

# Configuración de la app de Slack
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
register_actions(app)
handler = SlackRequestHandler(app)

# --- Punto de entrada para Google Cloud Functions ---
@functions_framework.http
def slack_request(request):
    # Challenge de Slack para verificar endpoint
    if request.method == "POST":
        data = request.get_json(silent=True)
        if data and data.get("type") == "url_verification":
            return (json.dumps({"challenge": data["challenge"]}), 200, {"Content-Type": "application/json"})
    if request.method in ["GET", "HEAD"]:
        return ("OK", 200)
    # Slack events handler
    return handler.handle(request)

# --- Eventos de Slack ---
@app.event("message")
def handle_message_events(event, say, client):
    if event.get("channel_type") != "im":
        return
    if event.get("subtype") == "bot_message":
        return

    user_id = event["user"]
    text = event.get("text", "").strip().lower()
    doc_ref = db.collection("conversations").document(user_id)
    state = doc_ref.get().to_dict() or {
        "data": {},
        "step": 0,
        "level": None,
        "flight_options": [],
        "hotel_options": [],
        "seen_flights": [],
        "seen_hotels": [],
    }

    # TIMEOUT: Si han pasado más de 30 min, reinicia estado
    state = reset_state_if_timeout(state)

    # 1. Bienvenida
    if handle_welcome(text, say, state, doc_ref):
        return

    # 2. Extracción y petición de datos mínimos
    datos = handle_extract_data(text, say, state, doc_ref, user_id)
    if datos is None:
        return

    # 3. Búsqueda de vuelos/hoteles y manejo de botones
    if handle_search_and_buttons(datos, state, event, client, say, doc_ref):
        return

    # 4. Resumen final, enviar a Finanzas
    handle_summary(datos, state, user_id, say, doc_ref, client)
