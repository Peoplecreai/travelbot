# search.py

import requests
from config import LODGING_LIMITS, get_region, SERPAPI_KEY

def search_google_flights(origin, destination, start_date, return_date):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": start_date,
        "return_date": return_date,
        "api_key": SERPAPI_KEY
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if 'best_flights' in data and data['best_flights']:
            return data['best_flights'][0]['flights']
    return []

def search_hotels(location, max_price):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_hotels",
        "q": f"hoteles en {location}",
        "currency": "USD",
        "api_key": SERPAPI_KEY,
        "max_price_per_night": max_price
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if 'properties' in data:
            return data['properties'][:3]
    return []

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

def get_flight_options(datos):
    # Regresa lista de vuelos (ya sea vacía o con opciones)
    flights = search_google_flights(
        datos['origin'], datos['destination'], datos['start_date'], datos['return_date']
    )
    return flights

def get_hotel_options(datos, state, max_lodging_override=None):
    region = get_region(datos['destination'])
    max_lodging = max_lodging_override or LODGING_LIMITS[state['level']][region]
    area = datos.get('venue') or datos['destination']

    # Verificar seguridad de la zona
    is_safe, info = check_safety(area)
    if not is_safe:
        better_area = find_better_area(area)
        area = better_area  # Buscar en la mejor zona alternativa

    hotels = search_hotels(area, max_lodging)
    return hotels, area, is_safe

# El archivo solo busca y entrega resultados a actions.py,
# NO manda mensajes ni botones aquí, eso se hace en actions.py
