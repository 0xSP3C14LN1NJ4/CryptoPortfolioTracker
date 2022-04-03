# Crypto Portfolio Tracker

This Crypto Portfolio Tracker helps you keep track of your current balances, see your transaction history, see your transfer history and make trades.

**This project is made for accounts on Gemini and the main currency used is Canadian dollars (CAD).**

## Installation and usage
- Clone this repository
```
$ git clone https://github.com/0xSP3C14LN1NJ4/CryptoPortfolioTracker.git
```

- Create `transactions.json` and `transfers.json` used to save data for transactions and transfers

- Generate an API Key on Gemini

- Create `api-key.txt` and `api-secret.txt` and type the Gemini API Key and the Gemini API Secret in their specific file

- Alternatively, if you want to use a sandbox account, create `api-key-test.txt` and `api-secret-test.txt` and type the API Key and the API Secret in their specific file

- Create an account on [Cryptowatch](cryptowat.ch) and generate an API Key

- Create `api-key-cw.txt` and type the Cryptowatch API Key

- In `config.py`, uncomment and comment the specific lines according to the account you want to use

- Run the project by running
```
$ python3 app.py
```

## Screenshots
NOTE : Unfortunately, I do not hold this much crypto. 🥲 These are screenshots from a sandbox account. 

- Portfolio Tab
![](screenshots/portfolio.png)

- Transactions Tab
![](screenshots/transactions.png)

- Transfers Tab
![](screenshots/transfers.png)

- Taxes Tab
![](screenshots/taxes.png)

- Trade Tab
![](screenshots/trade.png) 