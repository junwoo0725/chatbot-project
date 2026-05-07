import pandas as pd

chunksize = 100000
reservation_sessions = set()
print("Finding sessions with reservations...")
for chunk in pd.read_csv('/Users/junwoo/chatbot-project/logs.csv', chunksize=chunksize):
    reservation_sessions.update(chunk[chunk['event_type'] == 'reservation']['session_id'].unique())
    if len(reservation_sessions) > 10:
        break

reservation_sessions = list(reservation_sessions)[:5]
print("Found sessions:", reservation_sessions)

events = []
for chunk in pd.read_csv('/Users/junwoo/chatbot-project/logs.csv', chunksize=chunksize):
    events.append(chunk[chunk['session_id'].isin(reservation_sessions)])

df = pd.concat(events)
df = df.sort_values(['session_id', 'event_timestamp'])
print(df.to_string())
