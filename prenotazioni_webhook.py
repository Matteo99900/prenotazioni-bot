from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import json

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

        # Estrai parametri separati data e ora
        parameters = req.get('queryResult', {}).get('parameters', {})
        date = parameters.get('date')
        time = parameters.get('time')

        if not date or not time:
            return jsonify({'fulfillmentText': "Mi serve sia una data che un orario per completare la prenotazione."})

        # Costruisci datetime combinando data e ora
        datetime_str = f"{date}T{time}"
        start_time = datetime.fromisoformat(datetime_str)
        end_time = start_time + timedelta(minutes=30)

        # Crea evento sul calendario
        service = build("calendar", "v3", credentials=CREDS)
        event = {
            "summary": "Prenotazione",
            "start": {"dateTime": start_time.isoformat(), "timeZone": "Europe/Rome"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "Europe/Rome"},
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print("✅ Evento creato:", event.get("htmlLink"))

        return jsonify({
            "fulfillmentText": f"✅ Prenotazione confermata per il {start_time.strftime('%d %B %Y alle %H:%M')}."
        })

    except Exception as e:
        print("❌ Errore nel webhook:", e)
        return jsonify({"fulfillmentText": "Si è verificato un errore durante la prenotazione. Riprova più tardi."})

if __name__ == '__main__':
    app.run(debug=True)

