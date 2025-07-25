import requests
from config import LODGING_LIMITS, get_region, SERPAPI_KEY
from handlers.actions import post_flight_buttons, post_hotel_buttons

def check_safety(area):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": f"es segura la zona de {area}?",
        "api_key": SERPAPI_KEY
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if 'organic_results' in data and data['organic_results']:
            snippet = data['organic_results'][0].get('snippet', '')
            if "segura" in snippet.lower() or "safe" in snippet.lower():
                return True, snippet
            else:
                return False, snippet
    return False, "No se pudo verificar."

def find_better_area(area):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": f"zonas seguras cerca de {area}",
        "api_key": SERPAPI_KEY
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if 'organic_results' in data and data['organic_results']:
            return data['organic_results'][0].get('title', area)
    return area

def handle_search_and_buttons(datos, state, event, client, say, doc_ref, max_lodging_override=None):
    # Paso 1: Vuelos
    if not state.get('flight_selected'):
        flights = post_flight_buttons(datos, state, event, client, doc_ref)
        if flights:
            return True
        else:
            say("No encontré vuelos disponibles para esas fechas y rutas. Intenta con otros datos.")
            return True

    # Paso 2: Hoteles
    if not state.get('hotel_selected'):
        region = get_region(datos['destination'])
        max_lodging = max_lodging_override or LODGING_LIMITS[state['level']][region]
        area = datos.get('venue') or datos['destination']

        # --- Lógica de seguridad de zona ---
        is_safe, info = check_safety(area)
        if not is_safe:
            better_area = find_better_area(area)
            say(f"La zona {area} podría no ser segura: {info}. Buscaré hoteles en {better_area} en su lugar.")
            area = better_area

        hotels = post_hotel_buttons(datos, state, event, client, doc_ref, max_lodging, area=area)
        if hotels:
            return True
        else:
            say(f"No encontré hoteles en presupuesto. ¿Quieres buscar en otra zona o aumentar presupuesto?")
            return True
    return False
