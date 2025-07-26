import re
import requests
import airportsdata
from config import LODGING_LIMITS, get_region, SERPAPI_KEY

SERP_ENDPOINT = "https://serpapi.com/search.json"
AIRPORTS = airportsdata.load("IATA")


def _city_to_iata(city: str):
    for info in AIRPORTS.values():
        if info.get("city") and info["city"].lower() == city.lower():
            return info["iata"]
    return None


def _ensure_iata(value: str):
    if not value:
        return None
    val = value.strip().upper()
    if re.fullmatch(r"[A-Z]{3}", val) and val in AIRPORTS:
        return val
    return _city_to_iata(val)

def search_flights(datos, exclude_ids=None, query=None):
    """Search flights using SerpAPI Google Flights."""
    params = {"engine": "google_flights", "api_key": SERPAPI_KEY}
    if query:
        params["q"] = query
    else:
        dep = _ensure_iata(datos.get("origin"))
        arr = _ensure_iata(datos.get("destination"))
        if not dep or not arr:
            return [], f"No pude determinar el código IATA para {datos.get('origin')} o {datos.get('destination')}."
        params.update({
            "departure_id": dep,
            "arrival_id": arr,
            "outbound_date": datos["start_date"],
        })
        if datos.get("return_date"):
            params["return_date"] = datos["return_date"]
    try:
        resp = requests.get(SERP_ENDPOINT, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        if query is None:
            fallback = f"flights {datos.get('origin')} {datos.get('destination')} {datos.get('start_date')}"
            return search_flights(datos, exclude_ids=exclude_ids, query=fallback)
        return [], "Error consultando SerpAPI."

    flights = []
    for f in data.get("best_flights", []):
        fid = f"{f.get('airline','')} {f.get('flight_number','')} {f.get('departing_at','')}"
        if exclude_ids and fid in exclude_ids:
            continue
        flights.append({
            "id": fid,
            "airline": f.get("airline"),
            "flight_number": f.get("flight_number"),
            "departure_time": f.get("departing_at"),
            "arrival_time": f.get("arriving_at"),
            "price": f.get("price", {}).get("amount"),
        })
    if not flights:
        return [], "SerpAPI no devolvió vuelos."
    return flights, None


def search_hotels(datos, area, max_price, exclude_ids=None, query=None):
    """Search hotels using SerpAPI Google Hotels."""
    params = {
        "engine": "google_hotels",
        "api_key": SERPAPI_KEY,
        "check_in_date": datos["start_date"],
        "check_out_date": datos.get("return_date") or datos["start_date"],
    }
    if query:
        params["q"] = query
    else:
        params["q"] = area
    try:
        resp = requests.get(SERP_ENDPOINT, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        if query is None:
            fallback = f"hotels in {area}"
            return search_hotels(datos, area, max_price, exclude_ids, fallback)
        return [], "Error consultando SerpAPI."

    hotels = []
    for h in data.get("hotels_results", []):
        hid = h.get("name")
        if exclude_ids and hid in exclude_ids:
            continue
        price = h.get("price_night", {}).get("extracted")
        if price and price <= max_price:
            hotels.append({
                "id": hid,
                "name": h.get("name"),
                "price": price,
                "link": h.get("link"),
            })
    if not hotels:
        return [], "SerpAPI no devolvió hoteles."
    return hotels, None

def check_safety(area):
    queries = [
        f"es segura la zona de {area}?",
        f"{area} safety rating",
    ]
    snippets = []
    for q in queries:
        params = {"engine": "google", "q": q, "api_key": SERPAPI_KEY}
        try:
            resp = requests.get(SERP_ENDPOINT, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue
        if data.get("organic_results"):
            snippet = data["organic_results"][0].get("snippet", "")
            if snippet:
                snippets.append(snippet)
    info = " ".join(snippets)
    text = info.lower()
    if any(w in text for w in ["peligro", "insegura", "unsafe", "danger"]):
        return False, info or "No se encontró información."
    if any(w in text for w in ["segura", "safe"]):
        return True, info
    return False, info or "No se pudo verificar."

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
    from handlers.actions import post_flight_buttons, post_hotel_buttons

    state.setdefault('seen_flights', [])
    state.setdefault('seen_hotels', [])

    # Paso 1: Vuelos
    if not state.get('flight_selected'):
        flights, err = search_flights(datos, exclude_ids=state['seen_flights'])
        if err:
            say(err)
            return True
        if flights:
            post_flight_buttons(flights, state, event, client, doc_ref)
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

        hotels, err = search_hotels(datos, area, max_lodging, exclude_ids=state['seen_hotels'])
        if err:
            say(err)
            return True
        if hotels:
            post_hotel_buttons(hotels, state, event, client, doc_ref, area=area)
            return True
        else:
            say("No encontré hoteles en presupuesto. ¿Quieres buscar en otra zona o aumentar presupuesto?")
            return True
    return False
