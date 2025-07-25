# config.py

import os
from google.cloud import firestore
import google.generativeai as genai

# --- Variables de entorno obligatorias ---
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")

# --- Validaciones para debug ---
assert SLACK_BOT_TOKEN, "Falta SLACK_BOT_TOKEN"
assert SLACK_SIGNING_SECRET, "Falta SLACK_SIGNING_SECRET"
assert SERPAPI_KEY, "Falta SERPAPI_KEY"
assert GEMINI_API_KEY, "Falta GEMINI_API_KEY"
assert GOOGLE_SHEET_ID, "Falta GOOGLE_SHEET_ID"

print("✅ Config import ok, todas las variables de entorno presentes.")

# --- Inicializa Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini model cargado.")
except Exception as e:
    print(f"❌ Error cargando Gemini: {e}")
    model = None

# --- Firestore para persistencia de estado ---
try:
    db = firestore.Client()
    print("✅ Firestore client ok.")
except Exception as e:
    print(f"❌ Error inicializando Firestore: {e}")
    db = None

# --- Límites y reglas de política ---
PER_DIEM_RATES = {
    'México y Latinoamérica': 50,
    'EE.UU. y Canadá': 120,
    'Europa': 100
}

LODGING_LIMITS = {
    'C-Level': {
        'Nacional (México)': 150,
        'EE.UU. y Canadá': 200,
        'Latinoamérica': 180,
        'Europa': 250
    },
    'General': {
        'Nacional (México)': 75,
        'EE.UU. y Canadá': 150,
        'Latinoamérica': 120,
        'Europa': 180
    }
}

def get_region(destination):
    dest = destination.lower()
    if 'méxico' in dest:
        return 'Nacional (México)'
    if 'usa' in dest or 'estados unidos' in dest or 'canadá' in dest or 'canada' in dest:
        return 'EE.UU. y Canadá'
    if 'europa' in dest:
        return 'Europa'
    return 'Latinoamérica'
