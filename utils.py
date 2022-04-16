import requests
import json
import base64
import hmac
import time
import datetime
import hashlib

import config


def check_symbol(symbol):
    symbols = get_symbols()

    if symbol in symbols:
        return True


def get_symbols():
    endpoint = "/v1/symbols"
    url = config.base_url + endpoint
    symbols = requests.get(url).json()
    return symbols


def trade_request(action, action_quantity, convert_quantity, symbol):
    endpoint = "/v1/order/new"
    url = config.base_url + endpoint

    payload = {
        "request": endpoint,
        "nonce": get_nonce(),
        "symbol": symbol,
        "amount": action_quantity,
        "price": convert_quantity,
        "side": action,
        "type": "exchange limit",
        "options": ["maker-or-cancel"],
        "account": config.account
    }

    return execute_request(payload, url)


def execute_request(payload, url):
    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(config.gemini_api_secret, b64,
                         hashlib.sha384).hexdigest()

    request_headers = {'Content-Type': "text/plain",
                       'Content-Length': "0",
                       'X-GEMINI-APIKEY': config.gemini_api_key,
                       'X-GEMINI-PAYLOAD': b64,
                       'X-GEMINI-SIGNATURE': signature,
                       'Cache-Control': "no-cache"}

    response = requests.post(url, data=None, headers=request_headers)
    return response.json()


def get_nonce():
    t = datetime.datetime.now()
    payload_nonce = str(int(round(time.time() * 1000)))
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
        fee_usd_value = item['fee_usd_value']

        date = item['date']
        space_index = date.index(' ')
        date_str = date[0:space_index]
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        start_date = date - datetime.timedelta(days=4)
        start_date_str = datetime.datetime.strftime(start_date, '%Y-%m-%d')

        url = 'https://www.bankofcanada.ca/valet/observations/FX{}{}?order_dir=desc&start_date={}&end_date={}'.format(
            currency, config.LOCAL_CURRENCY, start_date_str, date_str)
        response = requests.get(url)
        value = response.json()["observations"][0]['fx{}{}'.format(
            currency, config.LOCAL_CURRENCY).upper()]['v']
        item['cad_value'] = float(value) * float(usd_value)
        item['fee_cad_value'] = float(value) * float(fee_usd_value)

    return data


def get_usd_value(data):
    for item in data:
        price = 1
        amount = item['amount']
        fee_amount = 0

        if item['type'] == 'Buy' or item['type'] == 'Sell':
            price = item['price']
            currency = item['fee_currency']
            quantity = price
            fee_amount = item['fee_amount']
        else:
            currency = item['currency']
            quantity = 1

        if currency != "USD":
            ts = item['timestampms']
            item['usd_value'] = get_usd_amount(quantity, amount, currency, ts)
            item['fee_usd_value'] = get_usd_amount(fee_amount, 1, currency, ts)
        else:
            item['usd_value'] = float(amount) * float(price)
            item['fee_usd_value'] = float(fee_amount)
    return data


def get_usd_amount(quantity, amount, currency, date):
    start_ts = int(float(date)/1000)
    end_ts = int(start_ts + 3600)
    period = 3600

    params = {
        'after': start_ts,
        'before': end_ts,
        'periods': period
    }

    headers = {
        'X-CW-API-Key': config.cryptowatch_api_key
    }

    response = requests.get(
        f'{config.cryptowatch_url}/{currency}usd/ohlc', params=params, headers=headers)
    usd_value = response.json(
    )['result'][f'{period}'][0][1] * float(quantity) * float(amount)
    return usd_value


def get_cad_unit_cost(data):
    for item in data:
        item['cad_unit_cost'] = item['cad_value'] / float(item['amount'])

    return data


def get_years():
    years = []

    current_year = datetime.date.today().year

    for year in range(current_year, 2020, -1):
        years.append(year)

    return years


def get_year_data(data, year):
    year_data = []

    for item in data:
        item_date = item['date']
        item_year = item_date[0:4]

        if item_year == year:
            year_data.append(item)

    return year_data


def get_last_previous_year(data, current_year):
    last_year = int(current_year) - 1
    data = sorted(data, key=lambda d: d['timestampms'], reverse=True)
    last_item = {
        "total_income": 0,
        "total_gain_loss": 0,
        "buy_sell_profit": 0
    }

    for item in data:
        item_date = item['date']
        item_year = int(item_date[0:4])

        if item_year == last_year:
            last_item = item
            break

    return last_item


def get_pricefeed():
    endpoint = "/v1/pricefeed"
    url = config.base_url + endpoint

    response = requests.get(url)
    return response.json()


def get_currencies(data):
    currencies = []

    for currency in data:
        currencies.append(
            {"currency": currency['currency'], "type": currency['type']})

    return currencies


def get_current_cad_value(usd_price):
    symbol = "usdcad"
    url = 'https://www.bankofcanada.ca/valet/observations/FX{}?recent=1'.format(symbol)
    response = requests.get(url)
    value = response.json()["observations"][0]['fx{}'.format(symbol).upper()]['v']

    return float(value) * float(usd_price)


def get_current_price(item, prices):
    currency = item['currency']

    for symbol in prices:
        pair = symbol['pair']

        if pair == currency + "USD":
            item['price'] = symbol['price']
            item['price_cad'] = get_current_cad_value(float(item['price']))
            item['percentChange24h'] = float(symbol['percentChange24h']) * 100

    return item


def get_current_prices(data):
    currencies = get_currencies(data)
    prices = get_pricefeed()

    for currency in currencies:
        type = currency['type']

        if type == "crypto":
            currency = get_current_price(currency, prices)
    return currencies


def get_balances():
    endpoint = "/v1/notionalbalances/{}".format(config.LOCAL_CURRENCY)
    url = config.base_url + endpoint
    total_balance = 0

    payload = {
        "nonce": get_nonce(),
        "request": endpoint,
        "account": config.account
    }

    balances = execute_request(payload, url)

    balances = sorted(balances, key=lambda d: d['amountNotional'], reverse=True)

    return balances


def get_transactions():
    endpoint = "/v1/mytrades"
    url = config.base_url + endpoint

    payload = {
        "nonce": get_nonce(),
        "request": endpoint,
        "account": config.account
    }

    transactions = execute_request(payload, url)
    transactions = timestamps_to_dates(transactions)

    for transaction in transactions:
        symbol = transaction['symbol']
        fee_currency = transaction['fee_currency']
        transaction['currency'] = symbol.replace(fee_currency, "")

    transactions = get_usd_value(transactions)
    transactions = get_cad_value(transactions)
    transactions = get_cad_unit_cost(transactions)

    with open(config.TRANSACTIONS_FILE, 'w') as file:
        json.dump(transactions, file)

    return transactions


def get_transfers():
    endpoint = "/v1/transfers"
    url = config.base_url + endpoint

    payload = {
        "nonce": get_nonce(),
        "request": endpoint,
        "account": config.account,
        "limit_transfers": 50 # TODO multiple calls to get all transfers
    }

    transfers = execute_request(payload, url)
    transfers = timestamps_to_dates(transfers)
    transfers = get_usd_value(transfers)
    transfers = get_cad_value(transfers)
    transfers = get_cad_unit_cost(transfers)

    with open(config.TRANSFERS_FILE, 'w') as file:
        json.dump(transfers, file)

    return transfers