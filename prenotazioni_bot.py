from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# === CONFIGURAZIONE ===
SERVICE_ACCOUNT_FILE = 'calendar-ai-456714-dc39022433cb.json'
CALENDAR_ID = 'rispostavocale@gmail.com'

SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('calendar', 'v3', credentials=creds)

# === PRENOTAZIONE: esempio per il 15 aprile 2025, ore 10:00 ===
start_time = datetime(2025, 4, 15, 10, 0)
end_time = start_time + timedelta(hours=1)

# === CONTROLLA DISPONIBILITÀ ===
events_result = service.events().list(
    calendarId=CALENDAR_ID,
    timeMin=start_time.isoformat() + 'Z',
    timeMax=end_time.isoformat() + 'Z',
    singleEvents=True,
    orderBy='startTime'
).execute()

events = events_result.get('items', [])

if events:
    print("❌ Orario già occupato. Scegli un altro slot.")
else:
    # === CREA L’EVENTO ===
    event = {
        'summary': 'Prenotazione cliente',
        'description': 'Prenotazione automatica ricevuta dal bot',
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Europe/Rome'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Rome'}
    }

    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print(f"✅ Prenotazione confermata! Evento ID: {created_event['id']}")
