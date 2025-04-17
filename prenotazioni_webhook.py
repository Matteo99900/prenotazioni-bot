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

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        req = request.get_json(force=True)
        print("📩 Richiesta ricevuta:", json.dumps(req, indent=2))

        # Estraggo i parametri
        parameters = req.get('queryResult', {}).get('parameters', {})
        datetime_str = parameters.get('date-time')

        if not datetime_str:
            return jsonify({"fulfillmentText": "Mi serve una data e un orario per fare la prenotazione."})

        # Converto la stringa ISO in oggetto datetime
        start_time = datetime.fromisoformat(datetime_str)
        end_time = start_time + timedelta(hours=1)

        # Carico le credenziali dalle variabili d’ambiente
        creds_json = os.environ.get("GOOGLE_CREDS_JSON")
        if not creds_json:
            raise Exception("Variabile d'ambiente GOOGLE_CREDS_JSON non trovata.")
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

        # Costruisco il servizio Google Calendar
        service = build('calendar', 'v3', credentials=creds)

        # Controllo se ci sono eventi sovrapposti
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=start_time.isoformat() + 'Z',
            timeMax=end_time.isoformat() + 'Z',
            singleEvents=True
        ).execute()

        events = events_result.get('items', [])

        if events:
            return jsonify({"fulfillmentText": "❌ L'orario è già occupato. Vuoi provare un altro orario?"})

        # Creo l'evento
        event = {
            'summary': 'Prenotazione cliente da Dialogflow',
            'description': 'Prenotazione automatica ricevuta dal bot',
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Europe/Rome'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Rome'}
        }

        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return jsonify({
            "fulfillmentText": f"✅ Prenotazione confermata per le {start_time.strftime('%H:%M del %d/%m/%Y')}"
        })

    except Exception as e:
        print(f"🚨 Errore nel webhook: {e}")
        return jsonify({"fulfillmentText": "Si è verificato un errore durante la prenotazione. Riprova più tardi."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
