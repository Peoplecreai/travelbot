from google.cloud import firestore

def post_flight_buttons(datos, state, event, client, doc_ref):
    # Aquí deberías tener tu lógica de búsqueda de vuelos
    # flights = search_google_flights(...) 
    flights = []  # Modifica esta línea por la función real
    # Suponiendo flights = [{"airline":..., "flight_number":..., ...}]
    if not flights:
        return None

    state['flight_options'] = flights
    buttons = []
    for i, f in enumerate(flights):
        label = f"{f['airline']} {f['flight_number']} {f['departure_time']} → {f['arrival_time']} ${f.get('price', 'N/A')}"
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": label[:75]},
            "value": str(i)
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

def post_hotel_buttons(datos, state, event, client, doc_ref, max_lodging, area=None):
    # Aquí deberías tener tu lógica de búsqueda de hoteles
    # hotels = search_hotels(...)
    hotels = []  # Modifica esta línea por la función real
    # Suponiendo hotels = [{"name":..., "price":...}]
    if not hotels:
        return None

    state['hotel_options'] = hotels
    buttons = []
    for i, h in enumerate(hotels):
        label = f"{h['name']} ({h.get('price', 'N/A')})"
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": label[:75]},
            "value": str(i)
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
