from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

# CONFIG
SERVICE_ACCOUNT_FILE = 'calendar-ai-456714-dc39022433cb.json'
CALENDAR_ID = 'rispostavocale@gmail.com'
SCOPES = ['https://www.googleapis.com/auth/calendar']

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    parameters = req['queryResult']['parameters']

    datetime_str = parameters.get('date-time')  # es: "2025-04-16T21:00:00+02:00"
    if not datetime_str:
        return jsonify({"fulfillmentText": "Mi serve una data e un orario per fare la prenotazione."})

    # Converte la stringa ISO in oggetto datetime
    start_time = datetime.fromisoformat(datetime_str)
    end_time = start_time + timedelta(hours=1)

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_time.isoformat() + 'Z',
        timeMax=end_time.isoformat() + 'Z',
        singleEvents=True
    ).execute().get('items', [])

    if events:
        return jsonify({"fulfillmentText": "❌ L'orario è già occupato. Vuoi provare un altro orario?"})
    else:
        event = {
            'summary': 'Prenotazione cliente da Dialogflow',
            'description': 'Prenotazione automatica ricevuta dal bot',
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Europe/Rome'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Rome'}
        }
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return jsonify({"fulfillmentText": f"✅ Prenotazione confermata per le {start_time.strftime('%H:%M del %d/%m/%Y')}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

