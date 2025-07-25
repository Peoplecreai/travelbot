user_id = event["user"]
    text = event.get("text", "").strip().lower()
    doc_ref = db.collection("conversations").document(user_id)
    state = doc_ref.get().to_dict() or {"data": {}, "step": 0, "level": None, "flight_options": [], "hotel_options": []}

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
