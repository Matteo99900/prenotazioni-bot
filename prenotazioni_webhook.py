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

        # Estrazione parametro
        parameters = req.get('queryResult', {}).get('parameters', {})
        datetime_str = parameters.get('date-time')

        if not datetime_str:
            return jsonify({'fulfillmentText': "Non ho capito quando vuoi prenotare. Puoi ripetere la data e l'ora?"})

        # Parsing della data
        try:
            start_time = datetime.fromisoformat(datetime_str)
        except Exception as e:
            print("⚠️ Errore parsing data:", str(e))
            return jsonify({'fulfillmentText': "Il formato della data non è valido."})

        end_time = start_time + timedelta(hours=1)

        # Caricamento credenziali da variabile ambiente
        credentials_json = os.environ.get("GOOGLE_CREDS_JSON")
        if not credentials_json:
            print("❌ Errore: nessuna credenziale trovata in GOOGLE_CREDS_JSON")
            return jsonify({'fulfillmentText': "Errore di configurazione. Riprovare più tardi."})

        credentials = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json),
            scopes=SCOPES
        )

        service = build("calendar", "v3", credentials=credentials)

        event = {
            "summary": "Prenotazione via Dialogflow",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "Europe/Rome",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "Europe/Rome",
            },
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"✅ Evento creato: {event.get('htmlLink')}")

        return jsonify({'fulfillmentText': "Prenotazione confermata per il " + start_time.strftime("%d %B %Y alle %H:%M")})

    except Exception as e:
        print("❌ Errore nel webhook:", str(e))
        return jsonify({'fulfillmentText': "Si è verificato un errore durante la prenotazione. Riprova più tardi."})

if __name__ == '__main__':
    app.run(debug=True)
