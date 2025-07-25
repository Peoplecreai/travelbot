# users.py

import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def map_to_policy_level(seniority):
    if "L8 - C-Level" in seniority:
        return "C-Level"
    return "General"

def load_user_levels():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.environ.get("GOOGLE_SHEET_ID")).sheet1
    data = sheet.get_all_records()
    user_levels = {}
    for row in data:
        slack_id = row.get('Slack_ID')
        seniority = row.get('Seniority')
        if slack_id and seniority:
            policy_level = map_to_policy_level(seniority)
            user_levels[slack_id] = policy_level
    return user_levels
