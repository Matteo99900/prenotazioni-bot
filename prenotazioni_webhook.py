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

        # Estrazione parametri
        parameters = req.get('queryResult', {}).get('parameters', {})
        datetime_str = parameters.get('date-time')

        if not datetime_str:
            return jsonify({'fulfillmentText': 'Non ho capito la data e l’orario della prenotazione.'})

        # Parsing data e ora
        start_time = datetime.fromisoformat(datetime_str)
        end_time = start_time + timedelta(hours=1)

        # Caricamento credenziali dal JSON in variabile d'ambiente
        creds_json = os.environ.get('GOOGLE_CREDS_JSON')
        if not creds_json:
            raise ValueError("GOOGLE_CREDS_JSON non trovata nelle variabili di ambiente.")

        service_account_info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )

        service = build('calendar', 'v3', credentials=credentials)

        # Crea evento
        event = {
            'summary': 'Nuova prenotazione',
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Europe/Rome'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Rome'},
        }

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print("✅ Evento creato:", created_event.get('htmlLink'))

        return jsonify({'fulfillmentText': 'Prenotazione registrata con successo!'})

    except Exception as e:
        print("❌ Errore nel webhook:", str(e))
        return jsonify({'fulfillmentText': 'Si è verificato un errore durante la prenotazione. Riprova più tardi.'})

