import pandas as pd
import numpy as np

# Load logs in chunks and process them
chunksize = 500000
log_file = '/Users/junwoo/chatbot-project/logs.csv'

print("Processing logs to generate shop scores...")
# We will use an iterative approach to keep memory usage low.
# Since we need to forward-fill search queries within sessions, 
# it's best to process the whole dataset if possible, or assume sessions are mostly contiguous.
# If they are not contiguous, we can sort them, but a 686MB file is small enough to load into memory with proper types.

types = {
    'event_type': 'category',
    'session_id': 'int32',
    'shop_id': 'string',
    'search_query': 'string'
}

df = pd.read_csv(log_file, usecols=['event_type', 'event_timestamp', 'session_id', 'shop_id', 'search_query'], dtype=types)

# Sort by session and time to forward fill search queries
print("Sorting data...")
df = df.sort_values(['session_id', 'event_timestamp'])

# Forward fill search query within each session
print("Forward filling search queries...")
# Replace empty string or NaN with NaN for ffill
df['search_query'] = df['search_query'].replace('', np.nan)
df['search_query'] = df.groupby('session_id')['search_query'].ffill()

# Drop rows without a search query (we can't attribute them to a query)
df = df.dropna(subset=['search_query'])

# Calculate weights
print("Calculating scores...")
weight_map = {
    'impression': 0.1,
    'click': 1.0,
    'view': 2.0,
    'bookmark': 10.0,
    'reservation': 50.0
}
df['score'] = df['event_type'].map(weight_map).astype(float)

# Group by search query and shop_id
print("Aggregating scores...")
shop_scores = df.groupby(['search_query', 'shop_id'])['score'].sum().reset_index()

# Sort by query and score descending
shop_scores = shop_scores.sort_values(['search_query', 'score'], ascending=[True, False])

output_file = '/Users/junwoo/chatbot-project/shop_scores.csv'
shop_scores.to_csv(output_file, index=False)
print(f"Shop scores successfully saved to {output_file}")
