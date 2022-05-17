LOCAL_CURRENCY = "cad"

TRANSACTIONS_FILE = "transactions.json"
TRANSFERS_FILE = "transfers.json"
DATA_FILE = "data.json"
CURRENCIES_FILE = "currencies.json"
BALANCES_FILE = "balances.json"
MANUAL_TRANSACTIONS_FILE = "manual_transactions.json"


# Sandbox account
"""
api_key_file = open("api-key-test.txt")
gemini_api_key = api_key_file.readline()
api_key_file.close()

api_secret_file = open("api-secret-test.txt")
gemini_api_secret = (api_secret_file.readline()).encode()
api_secret_file.close()

base_url = "https://api.sandbox.gemini.com"
"""

# Main account

api_key_file = open("api-key.txt")
gemini_api_key = api_key_file.readline()
api_key_file.close()

api_secret_file = open("api-secret.txt")
gemini_api_secret = (api_secret_file.readline()).encode()
api_secret_file.close()

base_url = "https://api.gemini.com"


account = "primary"


# Cryptowat.ch config
cryptowatch_url = "https://api.cryptowat.ch/markets/gemini"
cryptowatch_api_key_file = open("api-key-cw.txt")
cryptowatch_api_key = cryptowatch_api_key_file.readline()
cryptowatch_api_key_file.close()