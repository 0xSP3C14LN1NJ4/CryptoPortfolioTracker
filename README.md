# Crypto Portfolio Tracker

This Crypto Portfolio Tracker helps you keep track of your current balances, see your transaction history, see your transfer history and make trades.

**This project is made for accounts on Gemini and the main currency used is Canadian dollars (CAD).**

## Installation and usage
- Clone this repository
```
$ git clone https://github.com/0xSP3C14LN1NJ4/CryptoPortfolioTracker.git
```

- Create `transactions.json` and `transfers.json` used to save data for transactions and transfers

- Create `api-key.txt` and `api-secret.txt` and type the API Key and the API Secret in their specific file

- Alternatively, if you want to use a sandbox account, create `api-key-test.txt` and `api-secret-test.txt` and type the API Key and the API Secret in their specific file

- In `config.py`, uncomment and comment the specific lines according to the account you want to use

- Run the project by running
```
$ python3 app.py
```