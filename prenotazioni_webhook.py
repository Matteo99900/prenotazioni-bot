from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil import parser as dateutil_parser
import os
import json
import traceback

app = Flask(__name__)

# CONFIG
CALENDAR_ID = 'rispostavocale@gmail.com'
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDS = None

# Carica credenziali da variabile d'ambiente
try:
    raw_json = os.environ.get("GOOGLE_CREDS_JSON", "{}")
    raw_json = raw_json.replace('\\n', '\n')  # Corregge i newline nel campo private_key
    json_creds = json.loads(raw_json)
    CREDS = service_account.Credentials.from_service_account_info(json_creds, scopes=SCOPES)
except Exception as e:
    print("Errore nel caricamento delle credenziali:", e)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        req = request.get_json(force=True)
        print("📩 Richiesta ricevuta:", json.dumps(req, indent=2))

        parameters = req.get('queryResult', {}).get('parameters', {})
        date_raw = parameters.get('date')
        time_raw = parameters.get('time')

        if not date_raw or not time_raw:
            return jsonify({"fulfillmentText": "Mi serve sia la data che l'orario per fare la prenotazione."})

        # Parse separati e combinazione in datetime
        date_parsed = dateutil_parser.isoparse(date_raw).date()
        time_parsed = dateutil_parser.isoparse(time_raw).time()
        start_time = datetime.combine(date_parsed, time_parsed)
        end_time = start_time + timedelta(hours=1)

        service = build("calendar", "v3", credentials=CREDS)

        event = {
            "summary": "Prenotazione Dialogflow",
            "start": {"dateTime": start_time.isoformat(), "timeZone": "Europe/Rome"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "Europe/Rome"}
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print("✅ Evento creato:", event.get("htmlLink"))

        return jsonify({
            "fulfillmentText": f"✅ Prenotazione confermata per il {start_time.strftime('%d/%m/%Y alle %H:%M')}!"
        })

    except Exception as e:
        print("❌ Errore nel webhook:", str(e))
        traceback.print_exc()
        return jsonify({
            "fulfillmentText": "Si è verificato un errore durante la prenotazione. Riprova più tardi."
        })

if __name__ == '__main__':
    app.run(debug=True)