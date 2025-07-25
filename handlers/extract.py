import re
import dateparser
import dateparser.search

def extract_trip_data(text, datos_actuales=None):
    datos = datos_actuales or {}

    fechas = dateparser.search.search_dates(text, languages=['es'])
    if fechas and len(fechas) >= 2:
        datos['start_date'] = fechas[0][1].date().isoformat()
        datos['return_date'] = fechas[1][1].date().isoformat()
    elif fechas and len(fechas) == 1:
        datos['start_date'] = fechas[0][1].date().isoformat()

    if 'origin' not in datos or not datos['origin']:
        origen = re.search(r'(desde|de)\s+([A-Za-záéíóúüñ\s]+)', text, re.IGNORECASE)
        if origen:
            datos['origin'] = origen.group(2).strip()

    if 'destination' not in datos or not datos['destination']:
        destino = re.search(r'a\s+([A-Za-záéíóúüñ\s]+)', text, re.IGNORECASE)
        if destino:
            datos['destination'] = destino.group(1).strip()

    if 'motive' not in datos or not datos['motive']:
        motivo = re.search(r'(reunión|evento|conferencia|capacitaci[oó]n|visita|clientes?)', text, re.IGNORECASE)
        if motivo:
            datos['motive'] = motivo.group(0).capitalize()
    if 'venue' not in datos or not datos['venue']:
        venue = re.search(r'(oficinas? de [A-Za-z0-9\s]+)', text, re.IGNORECASE)
        if venue:
            datos['venue'] = venue.group(0)
    return datos

def handle_extract_data(text, say, state, doc_ref, user_id):
    datos = extract_trip_data(text, datos_actuales=state.get('data', {}))
    state['data'] = datos
    labels = {
        'destination': "Destino (ciudad y país)",
        'origin': "Origen (ciudad y país)",
        'start_date': "Fecha de salida",
        'return_date': "Fecha de regreso",
        'motive': "Motivo del viaje",
        'venue': "Nombre del evento o lugar (venue)"
    }
    fields_needed = [f"*{v}*" for k, v in labels.items() if not datos.get(k)]
    if fields_needed:
        resumen = [f"{v}: {datos[k]}" for k, v in labels.items() if datos.get(k)]
        msg = ""
        if resumen:
            msg += "Ya tengo:\n" + "\n".join(f"- {r}" for r in resumen) + "\n"
        msg += "Por favor indícame:\n" + "\n".join(f"• {f}" for f in fields_needed)
        say(msg)
        state['last_ts'] = datetime.datetime.utcnow().timestamp()
        doc_ref.set(state)
        return None
    return datos
