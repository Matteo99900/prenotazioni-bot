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
        date = parameters.get('date')
        time = parameters.get('time')

        if not date and not time:
            return jsonify({"fulfillmentText": "Non ho capito la data e l'orario della prenotazione."})

        # 🧠 Gestione robusta: se uno dei due parametri contiene già data+ora completa
        if 'T' in date:
            start_time = datetime.fromisoformat(date)
        elif 'T' in time:
            start_time = datetime.fromisoformat(time)
        else:
            datetime_str = f"{date}T{time}"
            start_time = datetime.fromisoformat(datetime_str)

        # Durata evento: 1 ora
        end_time = start_time + timedelta(hours=1)

        # Credenziali dal file JSON in variabile ambiente
        creds_data = os.getenv("GOOGLE_CREDS_JSON")
        if not creds_data:
            raise Exception("Variabile GOOGLE_CREDS_JSON non trovata.")
        creds_dict = json.loads(creds_data)
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": "Prenotazione Dialogflow",
            "start": {"dateTime": start_time.isoformat(), "timeZone": "Europe/Rome"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "Europe/Rome"},
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print("✅ Evento creato:", event.get("htmlLink"))

        return jsonify({
            "fulfillmentText": f"✅ Prenotazione confermata per il {start_time.strftime('%d/%m/%Y alle %H:%M')}!"
        })

    except Exception as e:
        print("❌ Errore nel webhook:", e)
        return jsonify({
            "fulfillmentText": "Si è verificato un errore durante la prenotazione. Riprova più tardi."
        })


if __name__ == '__main__':
    app.run(debug=True)
