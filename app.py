from flask import Flask, render_template, request
import json

import config
import utils


app = Flask(__name__)


@app.route('/')
def index():
    endpoint = "/v1/notionalbalances/{}".format(config.LOCAL_CURRENCY)
    url = config.base_url + endpoint
    total_balance = 0

    payload = {
        "nonce": utils.get_nonce(),
        "request": endpoint,
        "account": config.account
    }

    balances = utils.execute_request(payload, url)

    balances = sorted(balances, key=lambda d: d['amountNotional'], reverse=True)

    for currency in balances:
        total_balance = total_balance + float(currency['amountNotional'])
    return render_template("index.html", balances=balances, total_balance=total_balance)


@app.route('/transactions')
def transactions():
    transactions = []

    try:
        with open(config.TRANSACTIONS_FILE, 'r') as file:
            transactions = json.load(file)
    except:
        get_transactions()

        with open(config.TRANSACTIONS_FILE, 'r') as file:
            transactions = json.load(file)

    return render_template("transactions.html", transactions=transactions)


@app.route('/get-transactions', methods=["POST"])
def get_transactions():
    endpoint = "/v1/mytrades"
    url = config.base_url + endpoint

    payload = {
        "nonce": utils.get_nonce(),
        "request": endpoint,
        "account": config.account
    }

    transactions = utils.execute_request(payload, url)
    transactions = utils.timestamps_to_dates(transactions)

    for transaction in transactions:
        symbol = transaction['symbol']
        fee_currency = transaction['fee_currency']
        transaction['currency'] = symbol.replace(fee_currency, "")

    transactions = utils.get_usd_value(transactions)
    transactions = utils.get_cad_value(transactions)
    transactions = utils.get_cad_unit_cost(transactions)    

    with open(config.TRANSACTIONS_FILE, 'w') as file:
        json.dump(transactions, file)

    return render_template("transactions.html", transactions=transactions)


@app.route('/transfers')
def transfers():
    transfers = []

    try:
        with open(config.TRANSFERS_FILE, 'r') as file:
            transfers = json.load(file)
    except:
        get_transfers()

        with open(config.TRANSFERS_FILE, 'r') as file:
            transfers = json.load(file)

    return render_template("transfers.html", transfers=transfers)


@app.route('/get-transfers', methods=["POST"])
def get_transfers():
    endpoint = "/v1/transfers"
    url = config.base_url + endpoint

    payload = {
        "nonce": utils.get_nonce(),
        "request": endpoint,
        "account": config.account,
        "limit_transfers": 50
    }

    transfers = utils.execute_request(payload, url)
    transfers = utils.timestamps_to_dates(transfers)
    transfers = utils.get_usd_value(transfers)
    transfers = utils.get_cad_value(transfers)
    transfers = utils.get_cad_unit_cost(transfers)

    with open(config.TRANSFERS_FILE, 'w') as file:
        json.dump(transfers, file)

    return render_template("transfers.html", transfers=transfers)


@app.route('/taxes', methods=["GET", "POST"])
def taxes():
    all_data = []
    last_item = []
    previous_year_income = 0
    previous_year_gain_loss = 0
    previous_year_buy_sell_profit = 0

    with open(config.DATA_FILE, 'r') as file:
        all_data = json.load(file)

    if request.method == "POST" and "year" in request.form:
       year = request.form['year']
       last_previous_year_item = utils.get_last_previous_year(all_data, year)
       all_data = utils.get_year_data(all_data, year)
       previous_year_income = float(last_previous_year_item['total_income'])
       previous_year_gain_loss = float(last_previous_year_item['total_gain_loss'])
       previous_year_buy_sell_profit = float(last_previous_year_item['buy_sell_profit']) 
       
    last_item = all_data[-1]
    income = float(last_item['total_income']) - previous_year_income
    gain_loss = float(last_item['total_gain_loss']) - previous_year_gain_loss
    buy_sell_profit = float(last_item['buy_sell_profit']) - previous_year_buy_sell_profit
    taxable = float(income) + (float(gain_loss) / 2)

    return render_template("taxes.html", all_data=all_data, income=income, gain_loss=gain_loss, buy_sell_profit=buy_sell_profit, years=utils.get_years(), taxable=taxable)


@app.route('/trade')
def trade():
    endpoint = "/v1/orders"
    url = config.base_url + endpoint

    payload = {
        "nonce": utils.get_nonce(),
        "request": endpoint,
        "account": config.account
    }

    orders = utils.execute_request(payload, url)
    return render_template("trade.html", active_orders=orders, symbols=utils.get_symbols())


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

        if utils.check_symbol(symbol):
            details = utils.trade_request(action, quantity1, quantity2, symbol)
            message = 'Details : {}'.format(details)
        else:
            message = 'Invalid currencies!'

    return render_template('trade.html', message=message)


@app.route('/find-currencies', methods=['POST'])
def find_currencies():
    currency = request.form['currency1']
    symbols = utils.get_symbols()
    possible_currencies = []

    for symbol in symbols:
        if symbol.startswith(currency):
            possible_currencies.append(symbol.replace(currency, ''))

    return render_template('trade-form.html', possible_currencies=possible_currencies)


@app.route('/cancel-order', methods=['POST'])
def cancel_order():
    order_id = request.form['order_id']
    endpoint = "/v1/order/cancel"
    url = config.base_url + endpoint
    payload = {
        "nonce": utils.get_nonce(),
        "order_id": order_id,
        "request": endpoint,
        "account": config.account
    }

    order_cancelled = utils.execute_request(payload, url)
    return render_template('trade.html', order_cancelled=order_cancelled)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port="5050")
