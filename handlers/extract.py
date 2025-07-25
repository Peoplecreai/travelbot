import re
import dateparser
import dateparser.search
import datetime

def extract_trip_data(text, datos_actuales=None):
    datos = datos_actuales or {}

    # Fechas
    fechas = dateparser.search.search_dates(text, languages=['es'])
    if fechas and len(fechas) >= 2:
        datos['start_date'] = fechas[0][1].date().isoformat()
        datos['return_date'] = fechas[1][1].date().isoformat()
    elif fechas and len(fechas) == 1:
        datos['start_date'] = fechas[0][1].date().isoformat()

    # Origen
    if 'origin' not in datos or not datos['origin']:
        origen = re.search(r'(desde|de)\s+([A-Za-záéíóúüñ\s]+)', text, re.IGNORECASE)
        if origen:
            posibles = origen.group(2).strip()
            # Evita que tome palabras ambiguas como "agosto" como ciudad
            if posibles.lower() in ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']:
                datos['origin'] = None  # Ignora meses como origen
            else:
                datos['origin'] = posibles

    # Destino
    if 'destination' not in datos or not datos['destination']:
        destino = re.search(r'a\s+([A-Za-záéíóúüñ\s]+)', text, re.IGNORECASE)
        if destino:
            posibles = destino.group(1).strip()
            # Evita que tome meses como destino
            if posibles.lower() in ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']:
                datos['destination'] = None  # Ignora meses como destino
            else:
                datos['destination'] = posibles

    # Motivo
    if 'motive' not in datos or not datos['motive']:
        motivo = re.search(r'(reunión|evento|conferencia|capacitaci[oó]n|visita|clientes?)', text, re.IGNORECASE)
        if motivo:
            datos['motive'] = motivo.group(0).capitalize()

    # Venue
    if 'venue' not in datos or not datos['venue']:
        venue = re.search(r'(oficinas? de [A-Za-z0-9\s]+)', text, re.IGNORECASE)
        if venue:
            datos['venue'] = venue.group(0)

    return datos

def handle_extract_data(text, say, state, doc_ref, user_id):
    datos = extract_trip_data(text, datos_actuales=state.get('data', {}))
    state['data'] = datos

    # Origen
    if not datos.get('origin'):
        say("¿De dónde sales? Indícame la ciudad y país de origen de tu vuelo.")
        state['last_ts'] = datetime.datetime.utcnow().timestamp()
        doc_ref.set(state)
        return None

    # Destino
    if not datos.get('destination'):
        say("¿A qué ciudad viajas? Indícame destino con ciudad y país.")
        state['last_ts'] = datetime.datetime.utcnow().timestamp()
        doc_ref.set(state)
        return None

    # Fecha de salida
    if not datos.get('start_date'):
        say("¿Qué día sales de viaje? Dame la fecha de salida.")
        state['last_ts'] = datetime.datetime.utcnow().timestamp()
        doc_ref.set(state)
        return None

    # Fecha de regreso
    if not datos.get('return_date'):
        say("¿Cuándo regresas? Dame la fecha de regreso.")
        state['last_ts'] = datetime.datetime.utcnow().timestamp()
        doc_ref.set(state)
        return None

    # Motivo
    if not datos.get('motive'):
        say("¿Cuál es el motivo de tu viaje? Por ejemplo: reunión, evento, capacitación, visita, etc.")
        state['last_ts'] = datetime.datetime.utcnow().timestamp()
        doc_ref.set(state)
        return None

    # Venue
    if not datos.get('venue'):
        say("¿Dónde se llevará a cabo el evento o visita? Dame el nombre del lugar o evento.")
        state['last_ts'] = datetime.datetime.utcnow().timestamp()
        doc_ref.set(state)
        return None

    # Si llegó aquí, ya tiene todo
    return datos
