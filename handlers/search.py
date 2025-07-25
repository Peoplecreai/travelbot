# actions.py

from slack_sdk.web import WebClient

# Presenta botones de vuelo al usuario
def post_flight_buttons(datos, state, event, client: WebClient, doc_ref, flights=None):
    # Si no recibe la lista de vuelos, la busca aquí (pero mejor pásala por parámetro)
    if flights is None:
        from handlers.search import get_flight_options
        flights = get_flight_options(datos)

    if not flights:
        return False

    options = []
    for idx, flight in enumerate(flights):
        label = f"{flight.get('airline', '')} {flight.get('flight_number', '')} {flight.get('departure_time', '')} → {flight.get('arrival_time', '')} ${flight.get('price', 'N/A')}"
        options.append({
            "type": "button",
            "text": {"type": "plain_text", "text": label[:75]},
            "value": str(idx)
        })
    client.chat_postMessage(
        channel=event['channel'],
        text="Elige el vuelo que prefieres:",
        blocks=[{
            "type": "actions",
            "block_id": "flight_select",
            "elements": options
        }]
    )
    state['flight_options'] = flights
    doc_ref.set(state)
    return True

# Presenta botones de hotel al usuario
def post_hotel_buttons(datos, state, event, client: WebClient, doc_ref, max_lodging, area, hotels=None):
    if hotels is None:
        from handlers.search import get_hotel_options
        hotels, _, _ = get_hotel_options(datos, state, max_lodging_override=max_lodging)
    if not hotels:
        return False

    options = []
    for idx, hotel in enumerate(hotels):
        label = f"{hotel.get('name', '')} ({hotel.get('price', 'N/A')})"
        options.append({
            "type": "button",
            "text": {"type": "plain_text", "text": label[:75]},
            "value": str(idx)
        })
    client.chat_postMessage(
        channel=event['channel'],
        text=f"Elige el hotel que prefieres en {area}:",
        blocks=[{
            "type": "actions",
            "block_id": "hotel_select",
            "elements": options
        }]
    )
    state['hotel_options'] = hotels
    doc_ref.set(state)
    return True
