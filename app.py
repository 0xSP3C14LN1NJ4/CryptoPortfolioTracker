from flask import Flask, render_template, request
import json

import config
import utils
import cost_basis

app = Flask(__name__)


@app.route('/')
def index():
    with open(config.BALANCES_FILE, 'r') as file:
        balances = json.load(file)

    try:
        with open(config.CURRENCIES_FILE, 'r') as file:
            currencies = json.load(file)
    except:
        currencies = []

    current_prices = utils.get_current_prices(currencies)

    total_balance = 0
    for currency in balances:
        total_balance = total_balance + float(currency['amountNotional'])
    return render_template("index.html", balances=balances, total_balance=total_balance, currencies=currencies, current_prices=current_prices)


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
    transactions = utils.get_transactions()

    return render_template("transactions.html", transactions=transactions)


@app.route('/add-transaction', methods=["POST"])
def add_transaction():
    return render_template("add_transaction.html")


@app.route('/add-transaction-form', methods=["POST"])
def add_transaction_form():
    message = ""

    if 'exchange' in request.form and 'date' in request.form and 'time' in request.form and 'action' in request.form and 'quantity1' in request.form and 'currency1' in request.form and 'quantity2' in request.form and 'currency2' in request.form:
        exchange = request.form['exchange']
        date = request.form['date']
        time = request.form['time']

        action = request.form['action']
        quantity1 = request.form['quantity1']
        currency1 = request.form['currency1']

        quantity2 = request.form['quantity2']
        currency2 = request.form['currency2']

        fee = request.form['fee']
        fee_currency = request.form['fee-currency']

        symbol = currency1 + currency2

        if utils.check_symbol(symbol) and (fee_currency == currency1 or fee_currency == currency2):
            details = utils.add_transaction(
                exchange, date, time, action, quantity1, quantity2, symbol, fee, fee_currency)
            message = 'Details : {}'.format(details)
        else:
            message = 'Invalid currencies!'

    return render_template('transactions.html', message=message)


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
    transfers = utils.get_transfers()

    return render_template("transfers.html", transfers=transfers)


@app.route('/taxes', methods=["GET", "POST"])
def taxes():
    all_data = []
    last_item = []
    previous_year_income = 0
    previous_year_gain_loss = 0
    previous_year_buy_sell_profit = 0
    year = "all"

    with open(config.DATA_FILE, 'r') as file:
        all_data = json.load(file)

    if request.method == "POST" and "year" in request.form:
        year = request.form['year']
        if year != "all":
            last_previous_year_item = utils.get_last_previous_year(
                all_data, year)
            all_data = utils.get_year_data(all_data, year)
            previous_year_income = float(
                last_previous_year_item['total_income'])
            previous_year_gain_loss = float(
                last_previous_year_item['total_gain_loss'])
            previous_year_buy_sell_profit = float(
                last_previous_year_item['buy_sell_profit'])

    last_item = all_data[-1]
    income = float(last_item['total_income']) - previous_year_income
    gain_loss = float(last_item['total_gain_loss']) - previous_year_gain_loss
    buy_sell_profit = float(
        last_item['buy_sell_profit']) - previous_year_buy_sell_profit
    taxable = float(income) + (float(gain_loss) / 2)

    return render_template("taxes.html", all_data=all_data, income=income, gain_loss=gain_loss, buy_sell_profit=buy_sell_profit, years=utils.get_years(), year=year, taxable=taxable)


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
    # TODO errors messages
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
