# TravelBot

Slack bot for handling internal travel requests at Creai.

## Requirements

- Python 3.11+
- Dependencies from `requirements.txt`
- Slack Bolt, Functions Framework, Firestore client and Google Generative AI
- Google Cloud project with Firestore enabled
- SerpAPI key for flight and hotel search
- Gemini API key for conversation extraction
- A Google Sheet containing user data (via `GOOGLE_SHEET_ID`)

## Environment Variables

The app expects several environment variables when running:

- `SLACK_BOT_TOKEN` – token for your Slack bot user.
- `SLACK_SIGNING_SECRET` – Slack signing secret for verifying requests.
- `SERPAPI_KEY` – SerpAPI key used to query Google Flights/Hotels.
- `GEMINI_API_KEY` – Google Generative AI key (Gemini).
- `GOOGLE_SHEET_ID` – ID of the Google Sheet with user levels.
- `FINANCE_CHANNEL` – Slack channel where summaries are posted (defaults to `#travel-requests`).
- `GOOGLE_APPLICATION_CREDENTIALS` – path to a service account JSON with Firestore and Sheets permissions.

A service account JSON named `service-account.json` is required so `gspread` can read your Google Sheet.

## Running Locally

Install dependencies and export the required variables. Then start the bot using `functions-framework`:

```bash
pip install -r requirements.txt
functions-framework --target=slack_request --port=8080
```

The Slack app must be configured to send events to `http://localhost:8080/`.

## Tests

Run unit tests using `pytest`:

```bash
pytest
```
