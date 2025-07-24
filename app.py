import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import smtplib
from email.message import EmailMessage
import datetime
import requests  # Para llamadas a APIs como SerpAPI
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Tu clave de SerpAPI (reemplaza con la tuya)
SERPAPI_KEY = "bbf67f98b6e37efd7725e8fca40207f58a7c8ff5adf48fa6b31dce02cd12b609"  # Pega tu clave aquí

# Política de viajes (pégala completa aquí)
TRAVEL_POLICY = """
**Hospedaje, Vuelos y Viáticos**  
Vigencia: A partir de su implementación y sujeta a revisión anual.  

**Objetivo**  
Garantizar que los viajes de negocio se realicen de manera eficiente y bajo lineamientos claros que optimicen costos, manteniendo la comodidad y seguridad de los colaboradores.  

**Alcance**  
Aplica a todas las personas colaboradoras que viajen por razones laborales.  

**Lineamientos Generales**  
1. **Reservaciones y Autorizaciones**  
Todas las reservaciones de vuelos y hospedaje deben realizarse con al menos 7 días de anticipación.  
La persona colaboradora deberá completar previamente el Formulario de solicitud de viaje indicando:  
- Fechas del viaje  
- Motivo del viaje  
- Destino y duración  
- Opciones de hospedaje  
Sin la información completa no se autorizará el viaje.  
Tesorería es el responsable de buscar y contratar la mejor opción viable en tiempos y costo.  

2. **Vuelos**  
Los vuelos se reservarán en clase económica para todas las personas colaboradoras.  
Cualquier boleto en clase premier deberá contar con la autorización previa de la Presidencia.  

3. **Hospedaje**  
3.1 **Tarifas máximas por noche y destino**  
- C-Level (USD): Nacional (México) $150, EE.UU. y Canadá $200, Latinoamérica $180, Europa $250  
- General (USD): Nacional (México) $75, EE.UU. y Canadá $150, Latinoamérica $120, Europa $180  
3.2 **Habitación compartida**  
Para ciertos viajes o eventos podrá reservarse habitación compartida con otra persona colaboradora del mismo género, con el fin de fomentar la convivencia y optimizar costos.  

3.4 **Ubicación del hotel**  
Preferiblemente en zonas seguras y céntricas, cercanas al lugar de reuniones o eventos.  
Se evitarán zonas de alto riesgo o inseguridad.  

4. **Viáticos**  
4.1 **Asignación de viáticos**  
- País / Región: Viáticos diarios (USD)  
  - México y Latinoamérica: $50  
  - EE.UU. y Canadá: $120  
  - Europa: $100  
Deberá justificarse compartiendo el estado de cuenta de la tarjeta con que se haya efectuado el consumo o con redacción libre que incluya: fecha, concepto, monto y moneda, enviando el detalle a facturas@creai.mx.  
En visitas a CDMX el monto de viáticos diario puede variar cuando alguno de los alimentos sea cubierto por la empresa directamente o esté incluido en el hotel.  
El reembolso validado se depositará en el siguiente periodo de pago de nómina.  

5. **Estancias Prolongadas**  
Para viajes mayores a 7 noches se recomienda evaluar opciones de alquiler temporal, siempre dentro del rango presupuestal.  

6. **Proceso para la Autorización y Control**  
6.1 **Monitoreo y aprobaciones**  
Cada viaje debe contar con la autorización de Finanzas antes de comprar boletos o hacer reservaciones.  
Se dará preferencia a las aerolíneas, hoteles y/o proveedores con las que se tenga convenio empresarial.  
Si la reserva de hotel o vuelo excede los montos establecidos en esta política, deberá contar con la aprobación del Presidente de la Empresa.  
6.2 **Comprobantes de gasto**  
Consumos efectuados con medios empresariales dentro de México deberán cumplir con los requisitos fiscales locales.  
Debe apegarse a la guía de conducta ética. Cualquier abuso o alteración será sancionado.  

7. **Gastos No Cubiertos**  
- Hospedaje y gastos fuera de la fecha del evento oficial.  
- Servicio a la habitación (room service).  
- Minibar.  
- Servicios de spa, gimnasio o entretenimiento.  
- Transporte con destino diferente al negocio.  

8. **Casos Especiales**  
8.1 **Excepciones**  
Cualquier excepción a esta política deberá ser aprobada por la Presidencia antes del viaje.  

8.2 **Reservaciones Fuera de Tiempo**  
Solicitudes con menos de 7 días de anticipación se revisarán caso por caso y dependerán de la disponibilidad de tarifas adecuadas.  
"""

PER_DIEM_RATES = {'México y Latinoamérica': 50, 'EE.UU. y Canadá': 120, 'Europa': 100}
LODGING_LIMITS = {
    'C-Level': {'Nacional (México)': 150, 'EE.UU. y Canadá': 200, 'Latinoamérica': 180, 'Europa': 250},
    'General': {'Nacional (México)': 75, 'EE.UU. y Canadá': 150, 'Latinoamérica': 120, 'Europa': 180}
}

def get_region(destination):
    if 'México' in destination: return 'Nacional (México)'
    elif 'USA' in destination or 'Canadá' in destination or 'Canada' in destination: return 'EE.UU. y Canadá'
    elif 'Europa' in destination: return 'Europa'
    else: return 'Latinoamérica'

def calculate_per_diem(data):
    region = get_region(data['destination'])
    rate = PER_DIEM_RATES.get(region, 50)
    start = datetime.datetime.strptime(data['start_date'], '%Y-%m-%d')
    end = datetime.datetime.strptime(data['return_date'], '%Y-%m-%d')
    days = (end - start).days + 1
    total = rate * days
    if 'CDMX' in data['destination'] and data.get('meals_covered', False):
        total *= 0.8  # Ajuste ejemplo
    return total, rate

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
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'best_flights' in data:
            return data['best_flights'][0]['flights']  # Retorna el mejor vuelo
    return None  # Si falla, retorna None

def search_hotels(location, max_price):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_hotels",
        "q": f"hoteles en {location}",
        "currency": "USD",
        "api_key": SERPAPI_KEY,
        "max_price_per_night": max_price
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'properties' in data:
            return data['properties'][:3]  # Top 3 hoteles
    return None

def check_safety(area):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": f"es segura la zona de {area}?",
        "api_key": SERPAPI_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'organic_results' in data:
            snippet = data['organic_results'][0]['snippet']
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
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'organic_results' in data:
            return data['organic_results'][0]['title']
    return area  # Si no encuentra, usa la original

def map_to_policy_level(seniority):
    if "L8 - C-Level" in seniority:
        return "C-Level"
    else:
        return "General"

def load_user_levels():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1Wj2zVcQ7cKGirKc-TW68Eqg7OZrnquOnZnuSQI1fcEc").sheet1  # Reemplaza TU_SHEET_ID_AQUI con el ID de tu sheet
    data = sheet.get_all_records()
    user_levels = {}
    for row in data:
        slack_id = row.get('Slack_ID')  # Ajusta si tu columna se llama diferente
        seniority = row.get('Seniority')  # Ajusta si tu columna se llama diferente
        if slack_id and seniority:
            # Mapea el seniority detallado a policy level
            policy_level = map_to_policy_level(seniority)
            user_levels[slack_id] = policy_level
    return user_levels

def send_email(summary):
    msg = EmailMessage()
    msg['Subject'] = 'Nueva Solicitud de Viaje'
    msg['From'] = 'rh@creai.mx'
    msg['To'] = 'facturas@creai.mx'
    msg.set_content(summary)
    # Configura tu SMTP (ejemplo con Gmail, cambia según tu email)
    with smtplib.SMTP('smtp.gmail.com', 587) as s:
        s.starttls()
        s.login('tuemail@gmail.com', 'tupassword')  # Reemplaza con tus credenciales
        s.send_message(msg)

app = App(token=os.environ["SLACK_BOT_TOKEN"])
user_states = {}  # Estados de usuarios

@app.event("app_mention")
def handle_mention(event, say):
    user_id = event['user']
    text = event['text'].lower()
    if user_id not in user_states:
        user_states[user_id] = {'step': 0, 'data': {}, 'lang': 'es'}
    state = user_states[user_id]

    if 'nuevo viaje' in text or state['step'] == 0:
        # Extrae seniority automáticamente
        USER_LEVELS = load_user_levels()  # Carga desde Google Sheets
        level = USER_LEVELS.get(user_id, "General")  # Default General si no está
        state['data']['level'] = level
        say(f"¡Hola! Detecté tu nivel como {level}. Dime las fechas del viaje (ida: YYYY-MM-DD, vuelta: YYYY-MM-DD), motivo, destino (incluye venue como oficina/cliente), duración en días, y origen de vuelo.")
        state['step'] = 1
    elif state['step'] == 1:
        # Parsea input (asume usuario da info en texto, simplificado; en producción, usa parsing mejor)
        state['data']['start_date'] = "2025-08-10"  # Ejemplo, reemplaza con parsing real del texto del usuario
        state['data']['return_date'] = "2025-08-12"
        state['data']['motive'] = "Conferencia"
        state['data']['destination'] = "CDMX, oficina central"  # Ejemplo
        state['data']['origin'] = "GDL"
        state['data']['venue'] = state['data']['destination'].split(', ')[1] if ',' in state['data']['destination'] else state['data']['destination']

        # Búsqueda de vuelos
        flights = search_google_flights(state['data']['origin'], state['data']['destination'], state['data']['start_date'], state['data']['return_date'])
        if flights:
            say(f"Encontré vuelos: {flights[0]['departure_airport']['name']} a {flights[0]['arrival_airport']['name']} por aprox ${flights[0].get('price', 'N/A')}. ✈️")
        else:
            say("No encontré vuelos, Tesorería buscará manualmente.")

        # Límite de hospedaje
        region = get_region(state['data']['destination'])
        max_lodging = LODGING_LIMITS[state['data']['level']][region]

        # Chequeo de seguridad y hoteles
        area = state['data']['venue']
        is_safe, info = check_safety(area)
        if not is_safe:
            better_area = find_better_area(area)
            say(f"La zona {area} podría no ser segura: {info}. Sugiero {better_area} en su lugar.")
            area = better_area
        hotels = search_hotels(area, max_lodging)
        if hotels:
            hotel_sugs = "\n".join([f"- {h['name']} (${h.get('price', 'N/A')}/noche)" for h in hotels])
            say(f"Hoteles cerca de {area} dentro de ${max_lodging}: {hotel_sugs} 🏨")
        else:
            say("No encontré hoteles, Tesorería buscará.")

        # Continúa con viáticos, etc. (agrega el resto del flujo como en el código original)
        # Por brevedad, asume completa y envía
        summary = f"Solicitud de {user_id}\n- Nivel: {level}\n- Destino: {state['data']['destination']}\n- Vuelos: {flights}\n- Hoteles: {hotels}\n..."  # Completa summary
        app.client.chat_postMessage(channel='#travel-requests', text=summary)
        send_email(summary)
        say("¡Solicitud enviada!")
        del user_states[user_id]

# Reemplaza con tus tokens
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
