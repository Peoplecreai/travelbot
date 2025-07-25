# policy.py
import os

# Lee la política de viajes desde travel_policy.md (en el mismo folder)
def get_travel_policy():
    path = os.path.join(os.path.dirname(__file__), "travel_policy.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

TRAVEL_POLICY = get_travel_policy()
