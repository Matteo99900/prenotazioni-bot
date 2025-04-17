import os
import json
from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

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
            return jsonify({'fulfillmentText': "Non ho capito la data e l'orario."})

        event_datetime = datetime.fromisoformat(datetime_str)
        event_end = event_datetime + timedelta(hours=1)

        # 🔐 Caricamento credenziali da variabile d'ambiente
        google_creds_json = os.environ.get("GOOGLE_CREDS_JSON")
        if not google_creds_json:
            raise Exception("Variabile GOOGLE_CREDS_JSON non trovata.")

        creds_info = json.loads(google_creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)

        # Creazione servizio Google Calendar
        service = build("calendar", "v3", credentials=credentials)

        # 📅 Controllo eventi sovrapposti
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=event_datetime.isoformat() + 'Z',
            timeMax=event_end.isoformat() + 'Z',
            singleEvents=True
        ).execute()

        events = events_result.get('items', [])
        if events:
            return jsonify({'fulfillmentText': "❌ L'orario è già occupato. Vuoi provare un altro orario?"})

        # ✏️ Crea l'evento
        event = {
            'summary': 'Prenotazione da Dialogflow',
            'start': {'dateTime': event_datetime.isoformat(), 'timeZone': 'Europe/Rome'},
            'end': {'dateTime': event_end.isoformat(), 'timeZone': 'Europe/Rome'},
        }

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print("✅ Evento creato:", created_event['htmlLink'])

        return jsonify({'fulfillmentText': f"✅ Prenotazione confermata per le {event_datetime.strftime('%H:%M del %d/%m/%Y')}"})

    except Exception as e:
        print("❌ Errore nel webhook:", e)
        return jsonify({'fulfillmentText': "Si è verificato un errore durante la prenotazione. Riprova più tardi."})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
