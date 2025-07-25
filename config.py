# config.py

import os
from google.cloud import firestore
import google.generativeai as genai

# --- Variables de entorno ---
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")

# --- Inicializa Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Firestore para persistencia de estado ---
db = firestore.Client()

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

# --- Agrega esta función ---
def get_region(destination):
    dest = destination.lower()
    if 'méxico' in dest:
        return 'Nacional (México)'
    if 'usa' in dest or 'estados unidos' in dest or 'canadá' in dest or 'canada' in dest:
        return 'EE.UU. y Canadá'
    if 'europa' in dest:
        return 'Europa'
    return 'Latinoamérica'
