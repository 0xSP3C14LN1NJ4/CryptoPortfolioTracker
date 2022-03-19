import json

TRANSACTIONS_FILE = "transactions.json"
TRANSFERS_FILE = "transfers.json"

ALL_DATA_FILE = "all_data.json"



with open(TRANSACTIONS_FILE, 'r') as file:
    transactions = json.load(file)

with open(TRANSFERS_FILE, 'r') as file:
    transferts = json.load(file)

data = transactions + transferts
data = sorted(data, key=lambda d: d['timestampms'], reverse=True)

with open(ALL_DATA_FILE, 'w') as file:
    json.dump(data, file)