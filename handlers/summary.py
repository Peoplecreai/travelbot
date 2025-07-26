import datetime
from config import FINANCE_CHANNEL, db


def handle_summary(datos, state, user_id, say, doc_ref, client):
    if not datos.get('frequent_flyer'):
        say("¿Tienes número de viajero frecuente o membresía de hotel? Si no, responde 'no'.")
        state['step'] = 3
        state['last_ts'] = datetime.datetime.utcnow().timestamp()
        doc_ref.set(state)
        return

    summary = (
        f"Solicitud de {user_id}\n"
        f"- Nivel: {state['level']}\n"
        f"- Origen: {datos['origin']}\n"
        f"- Destino: {datos['destination']}\n"
        f"- Fechas: {datos['start_date']} a {datos['return_date']}\n"
        f"- Motivo: {datos['motive']}\n"
        f"- Venue: {datos['venue']}\n"
        f"- Vuelo: {state.get('flight_selected')}\n"
        f"- Hotel: {state.get('hotel_selected')}\n"
        f"- Viajero Frecuente: {datos.get('frequent_flyer','No')}\n"
    )
    client.chat_postMessage(channel=FINANCE_CHANNEL, text=summary)
    say("¡Listo! Tu solicitud ha sido enviada a Finanzas para la compra.")

    # Guardar ultimo destino en el perfil del usuario
    profile_ref = db.collection("profiles").document(user_id)
    profile_ref.set({"last_destination": datos["destination"]}, merge=True)

    # Reset state
    doc_ref.set({
        'data': {},
        'step': 0,
        'level': state['level'],
        'request_type': 'travel',
        'flight_options': [],
        'hotel_options': [],
        'seen_flights': [],
        'seen_hotels': [],
        'last_ts': state['last_ts'],
    })
