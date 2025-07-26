from handlers.extract import handle_extract_data
from handlers.search import handle_search_and_buttons
from handlers.summary import handle_summary


def determine_request_type(text: str) -> str:
    text = text.lower()
    if any(word in text for word in ["equipo", "laptop", "computadora"]):
        return "equipment"
    if "offboarding" in text or "baja" in text:
        return "offboarding"
    return "travel"


def handle_travel(event, say, client, state, doc_ref, user_id):
    text = event.get("text", "")
    datos = handle_extract_data(text, say, state, doc_ref, user_id)
    if datos is None:
        return
    if handle_search_and_buttons(datos, state, event, client, say, doc_ref):
        return
    handle_summary(datos, state, user_id, say, doc_ref, client)


def handle_request(event, say, client, state, doc_ref, user_id):
    request_type = state.get("request_type", "travel")
    if request_type == "travel":
        handle_travel(event, say, client, state, doc_ref, user_id)
    else:
        say(f"Aún no gestiono solicitudes de {request_type}. Próximamente podré ayudarte.")

