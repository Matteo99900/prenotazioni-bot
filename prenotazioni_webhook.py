from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import json
import dateparser

app = Flask(__name__)

# CONFIG
CALENDAR_ID = 'rispostavocale@gmail.com'
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDS = None

# Carica credenziali da variabile d'ambiente
try:
    json_creds = json.loads(os.environ.get("GOOGLE_CREDS_JSON", "{}"))
    CREDS = service_account.Credentials.from_service_account_info(json_creds, scopes=SCOPES)
except Exception as e:
    print("Errore nel caricamento delle credenziali:", e)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        req = request.get_json(force=True)
        print("📩 Richiesta ricevuta:", json.dumps(req, indent=2))

        # Estrai il testo originale
        query_text = req.get("queryResult", {}).get("queryText", "")
        print("🗣 Testo utente:", query_text)

        # Interpreta la data manualmente con dateparser
        parsed_date = dateparser.parse(query_text, languages=["it"])
        print("📅 Data interpretata:", parsed_date)

        if not parsed_date:
            raise ValueError("Impossibile interpretare la data dalla frase dell'utente.")

        start_time = parsed_date.isoformat()
        end_time = (parsed_date + timedelta(minutes=30)).isoformat()

        # Crea evento sul calendario
        service = build("calendar", "v3", credentials=CREDS)
        event = {
            "summary": "Prenotazione",
            "start": {"dateTime": start_time, "timeZone": "Europe/Rome"},
            "end": {"dateTime": end_time, "timeZone": "Europe/Rome"},
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print("✅ Evento creato:", event.get("htmlLink"))

        return jsonify({
            "fulfillmentText": f"Prenotazione effettuata per il {parsed_date.strftime('%d %B %Y alle %H:%M')}!"
        })

    except Exception as e:
        print("❌ Errore nel webhook:", e)
        return jsonify({"fulfillmentText": "Si è verificato un errore durante la prenotazione. Riprova più tardi."})

if __name__ == '__main__':
    app.run(debug=True)
