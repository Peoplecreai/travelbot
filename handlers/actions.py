# actions.py

def post_flight_buttons(datos, state, event, client, doc_ref, flights):
    """
    Muestra al usuario hasta 3 vuelos nuevos no mostrados antes.
    Si ya mostró todos, pregunta si tiene preferencia.
    """
    shown_flights = set(state.get('shown_flights', []))
    new_flights = [f for f in flights if f['flight_number'] not in shown_flights]

    if not new_flights:
        client.chat_postMessage(
            channel=event['channel'],
            text="No tengo más vuelos en esa ruta/fecha. ¿Tienes alguna aerolínea, horario o vuelo de preferencia? Dímelo, o responde 'no' para intentar nuevas opciones."
        )
        state['waiting_for_flight_preference'] = True
        doc_ref.set(state)
        return False

    options = new_flights[:3]
    buttons = []
    for f in options:
        label = f"{f['airline']} {f['flight_number']} {f['departure_time']} → {f['arrival_time']} ${f.get('price', 'N/A')}"
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": label[:75]},
            "value": f['flight_number']
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
    shown_flights.update([f['flight_number'] for f in options])
    state['shown_flights'] = list(shown_flights)
    state['waiting_for_flight_preference'] = False
    doc_ref.set(state)
    return True

def post_hotel_buttons(datos, state, event, client, doc_ref, hotels, area_info=None):
    """
    Muestra al usuario hasta 3 hoteles nuevos no mostrados antes.
    Si ya mostró todos, pregunta si tiene preferencia.
    """
    shown_hotels = set(state.get('shown_hotels', []))
    new_hotels = [h for h in hotels if h['name'] not in shown_hotels]

    if not new_hotels:
        client.chat_postMessage(
            channel=event['channel'],
            text="No tengo más hoteles disponibles. ¿Prefieres alguna zona, hotel o cadena? Dímelo, o responde 'no' para intentar nuevas opciones."
        )
        state['waiting_for_hotel_preference'] = True
        doc_ref.set(state)
        return False

    options = new_hotels[:3]
    buttons = []
    for h in options:
        price = h.get('price', 'N/A')
        label = f"{h['name']} ({price})"
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": label[:75]},
            "value": h['name']
        })

    area_note = f"\nNota: {area_info}" if area_info else ""
    client.chat_postMessage(
        channel=event['channel'],
        text="Elige el hotel que prefieres:" + area_note,
        blocks=[{
            "type": "actions",
            "block_id": "hotel_select",
            "elements": buttons
        }]
    )
    shown_hotels.update([h['name'] for h in options])
    state['shown_hotels'] = list(shown_hotels)
    state['waiting_for_hotel_preference'] = False
    doc_ref.set(state)
    return True

def handle_flight_select(ack, body, client, doc_ref, state):
    """
    Handler de botón de vuelo. Guarda la selección y avanza al flujo de hoteles.
    """
    ack()
    user_id = body['user']['id']
    value = body['actions'][0]['value']
    flights = state.get('flight_options', [])
    selected = next((f for f in flights if f['flight_number'] == value), None)
    if selected:
        state['flight_selected'] = selected
        doc_ref.set(state)
        client.chat_postMessage(
            channel=body['channel']['id'],
            text=f"Vuelo seleccionado: {selected['airline']} {selected['flight_number']}. ¿Listo para elegir hotel?"
        )

def handle_hotel_select(ack, body, client, doc_ref, state):
    """
    Handler de botón de hotel. Guarda la selección y avanza.
    """
    ack()
    user_id = body['user']['id']
    value = body['actions'][0]['value']
    hotels = state.get('hotel_options', [])
    selected = next((h for h in hotels if h['name'] == value), None)
    if selected:
        state['hotel_selected'] = selected
        doc_ref.set(state)
        client.chat_postMessage(
            channel=body['channel']['id'],
            text=f"Hotel seleccionado: {selected['name']}. ¿Tienes viajero frecuente o seguimos?"
        )

def handle_preference_response(state, event, say, doc_ref, preference_type):
    """
    Maneja cuando el usuario responde con una preferencia (vuelos u hoteles)
    """
    if preference_type == "flight":
        say("¡Perfecto! Buscaré vuelos que se ajusten a lo que pides.")
        # Aquí deberías re-disparar search.py con el filtro/preferencia nueva.
        state['waiting_for_flight_preference'] = False
    elif preference_type == "hotel":
        say("¡Perfecto! Buscaré hoteles que se ajusten a tu preferencia.")
        state['waiting_for_hotel_preference'] = False
    doc_ref.set(state)

def reset_options(state, doc_ref):
    """
    Limpia opciones ya mostradas (vuelos/hoteles) para empezar de cero.
    """
    state.pop('shown_flights', None)
    state.pop('shown_hotels', None)
    state['waiting_for_flight_preference'] = False
    state['waiting_for_hotel_preference'] = False
    doc_ref.set(state)
