import os
import flask
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from google.cloud import firestore

from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, db
from handlers.welcome import handle_welcome
from handlers.extract import handle_extract_data
from handlers.search import handle_search_and_buttons
from handlers.actions import register_actions
from handlers.summary import handle_summary
from utils.timeouts import reset_state_if_timeout

# Slack Bolt App
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
register_actions(app)
handler = SlackRequestHandler(app)

# Flask app for Cloud Run
flask_app = flask.Flask(__name__)

@flask_app.route("/slack/events", methods=["POST", "GET", "HEAD"])
def slack_events():
    if flask.request.method == "POST":
        data = flask.request.get_json(silent=True)
        if data and data.get("type") == "url_verification":
            return flask.jsonify({"challenge": data["challenge"]})
        return handler.handle(flask.request)
    else:
        return "OK", 200

@app.event("message")
def handle_message_events(event, say, client):
    if event.get("channel_type") != "im":
        return
    if event.get("subtype") == "bot_message":
        return

    user_id = event['user']
    text = event.get('text', '').strip().lower()
    doc_ref = db.collection('conversations').document(user_id)
    state = doc_ref.get().to_dict() or {'data': {}, 'step': 0, 'level': None, 'flight_options': [], 'hotel_options': []}

    # TIMEOUT: Si han pasado más de 30 min, reinicia estado
    state = reset_state_if_timeout(state)
    
    # 1. Bienvenida
    if handle_welcome(text, say, state, doc_ref):
        return

    # 2. Extracción y petición de datos mínimos
    datos = handle_extract_data(text, say, state, doc_ref, user_id)
    if datos is None:
        return  # Falta algún dato, ya se solicitó

    # 3. Búsqueda de vuelos/hoteles y manejo de botones
    if handle_search_and_buttons(datos, state, event, client, say, doc_ref):
        return

    # 4. Resumen final, enviar a Finanzas
    handle_summary(datos, state, user_id, say, doc_ref, client)

@app.event("app_home_opened")
def handle_app_home_opened(event, client, context):
    user_id = event["user"]
    client.views_publish(
        user_id=user_id,
        view={
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            "*¡Bienvenido a TravelBot!* :airplane:\n"
                            "Aquí puedes gestionar tus solicitudes de viajes de negocio según la política de la empresa.\n"
                            "Para empezar, escríbeme por este chat los detalles de tu próximo viaje o consulta los recursos en la barra lateral."
                        ),
                    },
                }
            ],
        },
    )

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=8080)

