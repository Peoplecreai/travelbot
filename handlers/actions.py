from google.cloud import firestore
from handlers.search import search_flights, search_hotels
from config import LODGING_LIMITS, get_region

def post_flight_buttons(flights, state, event, client, doc_ref):
    if not flights:
        return None

    state['flight_options'] = flights
    state.setdefault('seen_flights', [])
    state['seen_flights'].extend([f['id'] for f in flights])
    buttons = []
    for i, f in enumerate(flights):
        label = f"{f['airline']} {f['flight_number']} {f['departure_time']} → {f['arrival_time']} ${f.get('price', 'N/A')}"
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": label[:75]},
            "value": str(i),
            "action_id": "flight_select"
        })
    buttons.append({
        "type": "button",
        "text": {"type": "plain_text", "text": "Más opciones"},
        "value": "more",
        "action_id": "flight_reject"
    })
    buttons.append({
        "type": "button",
        "text": {"type": "plain_text", "text": "Sugerir vuelo"},
        "value": "suggest",
        "action_id": "flight_suggest"
    })
    client.chat_postMessage(
        channel=event['channel'],
        text="Elige el vuelo que prefieres:",
        blocks=[{
            "type": "actions",
            "block_id": "flight_select",
            "elements": buttons
        }]
    )
    doc_ref.set(state)
    return flights

def post_hotel_buttons(hotels, state, event, client, doc_ref, area=None):
    if not hotels:
        return None

    state['hotel_options'] = hotels
    state.setdefault('seen_hotels', [])
    state['seen_hotels'].extend([h['id'] for h in hotels])
    buttons = []
    for i, h in enumerate(hotels):
        label = f"{h['name']} ({h.get('price', 'N/A')})"
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": label[:75]},
            "value": str(i),
            "action_id": "hotel_select"
        })
    buttons.append({
        "type": "button",
        "text": {"type": "plain_text", "text": "Más opciones"},
        "value": "more",
        "action_id": "hotel_reject"
    })
    buttons.append({
        "type": "button",
        "text": {"type": "plain_text", "text": "Sugerir hotel"},
        "value": "suggest",
        "action_id": "hotel_suggest"
    })
    client.chat_postMessage(
        channel=event['channel'],
        text="¿Tienes preferencia de zona o cadena hotelera? Si no, elige uno de estos hoteles:",
        blocks=[{
            "type": "actions",
            "block_id": "hotel_select",
            "elements": buttons
        }]
    )
    doc_ref.set(state)
    return hotels

def register_actions(app):
    db = firestore.Client()
    @app.action("flight_select")
    def handle_flight_select(ack, body, client):
        ack()
        user_id = body['user']['id']
        value = int(body['actions'][0]['value'])
        doc_ref = db.collection('conversations').document(user_id)
        state = doc_ref.get().to_dict()
        selected_flight = state['flight_options'][value]
        state['flight_selected'] = selected_flight
        doc_ref.set(state)
        client.chat_postMessage(
            channel=body['channel']['id'],
            text=f"Vuelo seleccionado: {selected_flight['airline']} {selected_flight['flight_number']}. ¿Listo para elegir hotel?"
        )

    @app.action("hotel_select")
    def handle_hotel_select(ack, body, client):
        ack()
        user_id = body['user']['id']
        value = int(body['actions'][0]['value'])
        doc_ref = db.collection('conversations').document(user_id)
        state = doc_ref.get().to_dict()
        selected_hotel = state['hotel_options'][value]
        state['hotel_selected'] = selected_hotel
        doc_ref.set(state)
        client.chat_postMessage(
            channel=body['channel']['id'],
            text=f"Hotel seleccionado: {selected_hotel['name']}. ¿Tienes viajero frecuente o seguimos?"
        )

    @app.action("flight_reject")
    def handle_flight_reject(ack, body, client):
        ack()
        user_id = body['user']['id']
        doc_ref = db.collection('conversations').document(user_id)
        state = doc_ref.get().to_dict()
        state.setdefault('seen_flights', [])
        state['seen_flights'].extend([f['id'] for f in state.get('flight_options', [])])
        flights, err = search_flights(state['data'], exclude_ids=state['seen_flights'])
        if err:
            client.chat_postMessage(channel=body['channel']['id'], text=err)
        elif flights:
            post_flight_buttons(flights, state, {'channel': body['channel']['id']}, client, doc_ref)
        else:
            client.chat_postMessage(channel=body['channel']['id'], text="No encontré más vuelos disponibles.")

    @app.action("hotel_reject")
    def handle_hotel_reject(ack, body, client):
        ack()
        user_id = body['user']['id']
        doc_ref = db.collection('conversations').document(user_id)
        state = doc_ref.get().to_dict()
        state.setdefault('seen_hotels', [])
        state['seen_hotels'].extend([h['id'] for h in state.get('hotel_options', [])])
        region = get_region(state['data']['destination'])
        max_lodging = LODGING_LIMITS[state['level']][region]
        region_area = state['data'].get('venue') or state['data']['destination']
        hotels, err = search_hotels(state['data'], region_area, max_lodging, exclude_ids=state['seen_hotels'])
        if err:
            client.chat_postMessage(channel=body['channel']['id'], text=err)
        elif hotels:
            post_hotel_buttons(hotels, state, {'channel': body['channel']['id']}, client, doc_ref, area=region_area)
        else:
            client.chat_postMessage(channel=body['channel']['id'], text="No encontré más hoteles disponibles.")

    @app.action("flight_suggest")
    def handle_flight_suggest(ack, body, client):
        ack()
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "flight_suggest_submit",
                "title": {"type": "plain_text", "text": "Sugerir vuelo"},
                "submit": {"type": "plain_text", "text": "Enviar"},
                "close": {"type": "plain_text", "text": "Cancelar"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "flight_text",
                        "element": {"type": "plain_text_input", "action_id": "val"},
                        "label": {"type": "plain_text", "text": "Indica vuelo o aerolínea"}
                    }
                ]
            }
        )

    @app.view("flight_suggest_submit")
    def handle_flight_suggest_submit(ack, body, client):
        ack()
        user_id = body['user']['id']
        flight_query = body['view']['state']['values']['flight_text']['val']['value']
        doc_ref = db.collection('conversations').document(user_id)
        state = doc_ref.get().to_dict()
        flights, err = search_flights(state['data'], query=flight_query)
        if err:
            client.chat_postMessage(channel=user_id, text=err)
        elif flights:
            post_flight_buttons(flights, state, {'channel': user_id}, client, doc_ref)
        else:
            client.chat_postMessage(channel=user_id, text="No encontré disponibilidad para ese vuelo.")

    @app.action("hotel_suggest")
    def handle_hotel_suggest(ack, body, client):
        ack()
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "hotel_suggest_submit",
                "title": {"type": "plain_text", "text": "Sugerir hotel"},
                "submit": {"type": "plain_text", "text": "Enviar"},
                "close": {"type": "plain_text", "text": "Cancelar"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "hotel_text",
                        "element": {"type": "plain_text_input", "action_id": "val"},
                        "label": {"type": "plain_text", "text": "Nombre o zona del hotel"}
                    }
                ]
            }
        )

    @app.view("hotel_suggest_submit")
    def handle_hotel_suggest_submit(ack, body, client):
        ack()
        user_id = body['user']['id']
        hotel_query = body['view']['state']['values']['hotel_text']['val']['value']
        doc_ref = db.collection('conversations').document(user_id)
        state = doc_ref.get().to_dict()
        region = get_region(state['data']['destination'])
        max_lodging = LODGING_LIMITS[state['level']][region]
        region_area = state['data'].get('venue') or state['data']['destination']
        hotels, err = search_hotels(state['data'], region_area, max_lodging, query=hotel_query)
        if err:
            client.chat_postMessage(channel=user_id, text=err)
        elif hotels:
            post_hotel_buttons(hotels, state, {'channel': user_id}, client, doc_ref, area=region_area)
        else:
            client.chat_postMessage(channel=user_id, text="No encontré disponibilidad para ese hotel.")
