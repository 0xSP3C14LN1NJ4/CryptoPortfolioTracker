from flask import Flask, render_template, request
import time
import datetime
import json
import base64
import hmac
import hashlib
from graphviz import render
import requests


app = Flask(__name__)
LOCAL_CURRENCY = "cad"

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


@app.route('/')
def index():
    endpoint = "/v1/notionalbalances/{}".format(LOCAL_CURRENCY)
    url = base_url + endpoint
    total_balance = 0

    payload = {
        "nonce": get_nonce(),
        "request": endpoint,
        "account": account
    }

    balances = execute_request(payload, url)

    for currency in balances:
        total_balance = total_balance + float(currency['amountNotional'])
    return render_template("index.html", balances=balances, total_balance=total_balance)


@app.route('/transactions')
def transactions():
    endpoint = "/v1/mytrades"
    url = base_url + endpoint

    payload = {
        "nonce": get_nonce(),
        "request": endpoint,
        "account": account
    }

    transactions = execute_request(payload, url)
    transactions = timestamps_to_dates(transactions)

    for transaction in transactions:
        symbol = transaction['symbol']
        fee_currency = transaction['fee_currency']
        transaction['currency'] = symbol.replace(fee_currency, "")

    transactions = get_usd_value(transactions)
    transactions = get_cad_value(transactions)
    return render_template("transactions.html", transactions=transactions)


@app.route('/transfers')
def transfers():
    endpoint = "/v1/transfers"
    url = base_url + endpoint

    payload = {
        "nonce": get_nonce(),
        "request": endpoint,
        "account": account,
        "limit_transfers": 50
    }

    transfers = execute_request(payload, url)
    transfers = timestamps_to_dates(transfers)
    transfers = get_usd_value(transfers)
    transfers = get_cad_value(transfers)
    return render_template("transfers.html", transfers=transfers)


@app.route('/trade')
def trade():
    endpoint = "/v1/orders"
    url = base_url + endpoint

    payload = {
        "nonce": get_nonce(),
        "request": endpoint,
        "account": account
    }

    orders = execute_request(payload, url)
    return render_template("trade.html", active_orders=orders, symbols=get_symbols())


@app.route('/trade-form', methods=["POST"])
def trade_form():
    currency1 = request.form['currency1']
    message = ""

    if 'action' in request.form and 'quantity1' in request.form and 'quantity2' in request.form and 'currency2' in request.form:
        action = request.form['action']
        quantity1 = request.form['quantity1']

        quantity2 = request.form['quantity2']
        currency2 = request.form['currency2']

        symbol = currency1 + currency2

        if check_symbol(symbol):
            details = trade_request(action, quantity1, quantity2, symbol)
            message = 'Details : {}'.format(details)
        else:
            message = 'Invalid currencies!'

    return render_template('/trade.html', message=message)


@app.route('/find-currencies', methods=['POST'])
def find_currencies():
    currency = request.form['currency1']
    symbols = get_symbols()
    possible_currencies = []

    for symbol in symbols:
        if symbol.startswith(currency):
            possible_currencies.append(symbol.replace(currency, ''))

    return render('/trade-form.html', possible_currencies=possible_currencies)


@app.route('/cancel-order', methods=['POST'])
def cancel_order():
    order_id = request.form['order_id']
    endpoint = "/v1/order/cancel"
    url = base_url + endpoint
    payload = {
        "nonce": get_nonce(),
        "order_id": order_id,
        "request": endpoint,
        "account": account
    }

    order_cancelled = execute_request(payload, url)
    return render_template('/trade.html', order_cancelled=order_cancelled)


def check_symbol(symbol):
    symbols = get_symbols()

    if symbol in symbols:
        return True


def get_symbols():
    endpoint = "/v1/symbols"
    url = base_url + endpoint
    symbols = requests.get(url).json()
    return symbols


def trade_request(action, action_quantity, convert_quantity, symbol):
    endpoint = "/v1/order/new"
    url = base_url + endpoint

    payload = {
        "request": endpoint,
        "nonce": get_nonce(),
        "symbol": symbol,
        "amount": action_quantity,
        "price": convert_quantity,
        "side": action,
        "type": "exchange limit",
        "options": ["maker-or-cancel"],
        "account": account
    }

    return execute_request(payload, url)


def execute_request(payload, url):
    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

    request_headers = {'Content-Type': "text/plain",
                       'Content-Length': "0",
                       'X-GEMINI-APIKEY': gemini_api_key,
                       'X-GEMINI-PAYLOAD': b64,
                       'X-GEMINI-SIGNATURE': signature,
                       'Cache-Control': "no-cache"}

    response = requests.post(url, data=None, headers=request_headers)

    return response.json()


def get_nonce():
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple())*1000))
    return payload_nonce


def timestamps_to_dates(data):
    for item in data:
        item['date'] = datetime.datetime.fromtimestamp(
            item['timestampms']/1000).strftime('%Y-%m-%d %H:%M:%S')
        item['date_iso'] = datetime.datetime.fromtimestamp(
            item['timestampms']/1000).replace(microsecond=0).isoformat()
    return data


def get_cad_value(data):
    for item in data:
        currency = "usd"
        usd_value = item['usd_value']

        date = item['date']
        space_index = date.index(' ')
        date_str = date[0:space_index]
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        start_date = date - datetime.timedelta(days=4)
        start_date_str = datetime.datetime.strftime(start_date, '%Y-%m-%d')

        url = 'https://www.bankofcanada.ca/valet/observations/FX{}{}?order_dir=desc&start_date={}&end_date={}'.format(
            currency, LOCAL_CURRENCY, start_date_str, date_str)
        response = requests.get(url)
        value = response.json()["observations"][0]['fx{}{}'.format(
            currency, LOCAL_CURRENCY).upper()]['v']
        item['cad_value'] = float(value) * float(usd_value)

    return data


def get_usd_value(data):
    for item in data:
        price = 1
        amount = item['amount']

        if item['type'] == 'Buy' or item['type'] == 'Sell':
            price = item['price']
            currency= item['fee_currency']
            quantity = price
        else:
            currency = item['currency']
            quantity = amount


        if currency != "USD":
            item['usd_value'] = get_usd_amount(quantity, currency, item['timestampms'])
        else:
            item['usd_value'] = float(amount) * float(price)
    return data


def get_usd_amount(quantity, currency, date):
    start_ts = int(float(date)/1000)
    end_ts = int(start_ts + 3600)
    period = 3600

    params = {
        'after': start_ts,
        'before': end_ts,
        'periods': period,
    }

    response = requests.get(f'https://api.cryptowat.ch/markets/gemini/{currency}usd/ohlc',params=params)
    usd_value = response.json()['result'][f'{period}'][0][1] * float(quantity)
    return usd_value


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port="5050")
