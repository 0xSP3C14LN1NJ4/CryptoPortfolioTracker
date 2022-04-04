import json
from dateutil import parser
import datetime

import config
import utils


TYPE_DEPOSIT_STR = "Deposit"
TYPE_WITHDRAWAL_STR = "Withdrawal"
TYPE_ADMIN_CREDIT_STR = "AdminCredit"
TYPE_BUY_STR = "Buy"
TYPE_SELL_STR = "Sell"
STATUS_COMPLETE_STR = "Complete"
STATUS_ADVANCED_STR = "Advanced"

total_gain_loss = 0
total_income = 0

total_buy_cad = 0
total_sell_cad = 0

buy_sell_profit = 0

variables = []

try:
    with open(config.BALANCES_FILE, 'r') as file:
        balances = json.load(file)
except:
    balances = utils.get_balances()

for balance in balances:
    currency = balance['currency']

    if currency == "USD":
        type = "fiat"
    else:
        type = "crypto"
        
    variables.append({
        "currency": currency,
        "type": type,
        "list": [],
        "quantity": 0,
        "cad_value": 0,
        "quantity_buy": 0,
        "quantity_sell": 0,
        "cad_value_buy": 0,
        "cad_value_sell": 0,
        "usd_value_buy": 0,
        "usd_value_sell": 0 
    })

variables = sorted(variables, key=lambda d: d['currency'])


def merge_data():
    with open(config.TRANSACTIONS_FILE, 'r') as file:
        transactions = json.load(file)

    for transaction in transactions:
        transaction.pop("timestamp")
        transaction.pop("aggressor")
        transaction.pop("tid")
        transaction.pop("order_id")
        transaction.pop("exchange")
        transaction.pop("is_auction_fill")
        transaction.pop("is_clearing_fill")
        transaction.pop("date_iso")

    with open(config.TRANSFERS_FILE, 'r') as file:
        transfers = json.load(file)

    for transfer in transfers:
        type = transfer['type']
        status = transfer['status']

        transfer.pop("status")
        transfer.pop("eid")
        transfer.pop("date_iso")

        if type == TYPE_DEPOSIT_STR or type == TYPE_WITHDRAWAL_STR:
            transfer.pop("destination")

            if type == TYPE_DEPOSIT_STR and status == STATUS_COMPLETE_STR:
                transfer.pop("method")
                transfer.pop("source")
                transfer.pop("transferId")
            else:
                transfer.pop("txHash")

                if status == STATUS_ADVANCED_STR:
                    transfer.pop("outputIdx")
                else:
                    transfer.pop("withdrawalId")

    data = transactions + transfers
    data = sorted(data, key=lambda d: d['timestampms'])

    for item in data:
        current_currency = item["currency"]

        for currency in variables:
            if current_currency == currency['currency']:
                currency['list'].append(item)


def set_other_currency(item):
    fee_currency = item['fee_currency']
    type = item['type']
    amount = float(item['amount'])
    price = float(item['price'])
    cad_value = float(item['cad_value'])
    usd_value = float(item['usd_value'])

    for temp_currency in variables:
        temp_fee_currency = temp_currency['currency']

        if fee_currency == temp_fee_currency:
            if type == TYPE_BUY_STR:
                temp_currency['quantity'] -= price * amount
                temp_currency['cad_value'] -= cad_value
                temp_currency['quantity_sell'] -= price * amount
                temp_currency['cad_value_sell'] -= cad_value
                temp_currency['usd_value_sell'] -= usd_value
            elif type == TYPE_SELL_STR:
                temp_currency['quantity'] += price * amount
                temp_currency['cad_value'] += cad_value
                temp_currency['quantity_buy'] += price * amount
                temp_currency['cad_value_buy'] += cad_value
                temp_currency['usd_value_buy'] += usd_value


def get_cost_basis():
    for currency in variables:
        list = currency['list']
        currency_quantity = currency['quantity']
        currency_cad_value = currency['cad_value']
        total_sell_currency = 0

        for item in list:
            type = item['type']
            amount = float(item['amount'])
            cad_value = item['cad_value']
            usd_value = item['usd_value']
            fee_cad_value = item['fee_cad_value']
            item['total_buy_cad'] = 0
            item['total_sell_cad'] = 0
            item['total_buy_usd'] = 0
            item['total_sell_usd'] = 0

            if currency_quantity == 0:
                item['cost_basis'] = cad_value + fee_cad_value
            else:
                item['cost_basis'] = (currency_cad_value / currency_quantity) * amount

            if type == TYPE_WITHDRAWAL_STR or type == TYPE_DEPOSIT_STR or type == TYPE_BUY_STR or type == TYPE_ADMIN_CREDIT_STR:
                item['cost_basis'] = 0
                gain_loss = 0

                if type != TYPE_WITHDRAWAL_STR:
                    currency_quantity += amount
                    currency_cad_value += cad_value + fee_cad_value

                    if type == TYPE_BUY_STR:
                        set_other_currency(item)
                        currency['quantity_buy'] += amount
                        currency['cad_value_buy'] += cad_value
                        currency['usd_value_buy'] += usd_value

            elif type == TYPE_SELL_STR:
                currency_quantity -= amount
                currency_cad_value -= cad_value + fee_cad_value
                set_other_currency(item)
                gain_loss = cad_value - float(item['cost_basis'])
                total_sell_currency += amount
                currency['quantity_sell'] += amount
                currency['cad_value_sell'] += cad_value
                currency['usd_value_sell'] += usd_value

            currency['quantity'] = currency_quantity
            currency['cad_value'] = currency_cad_value
            item['gain_loss'] = gain_loss
            item['total_sell_currency'] = total_sell_currency
    
        if currency['quantity_buy'] != 0:
            currency['average_buy_cad'] = currency['cad_value_buy'] / currency['quantity_buy']
            currency['average_buy_usd'] = currency['usd_value_buy'] / currency['quantity_buy']

        if currency['quantity_sell'] != 0:
            currency['average_sell_cad'] = currency['cad_value_sell'] / currency['quantity_sell']
            currency['average_sell_usd'] = currency['usd_value_sell'] / currency['quantity_sell']


def add_totals(data):
    total_income = 0
    total_buy_cad = 0
    total_sell_cad = 0
    total_gain_loss = 0

    for item in data:
        type = item['type']
        cad_value = item['cad_value']
        gain_loss = item['gain_loss']

        if type == TYPE_DEPOSIT_STR or type == TYPE_ADMIN_CREDIT_STR:
            total_income += cad_value
        elif type == TYPE_BUY_STR:
            total_buy_cad += cad_value
        elif type == TYPE_SELL_STR:
            total_sell_cad += cad_value

        total_gain_loss += gain_loss

        item['total_income'] = total_income
        item['total_buy_cad'] = total_buy_cad
        item['total_sell_cad'] = total_sell_cad
        item['total_gain_loss'] = total_gain_loss
        item['buy_sell_profit'] = total_sell_cad - total_buy_cad

    return data


def check_superficial_loss(transaction, data):
    gain_loss = transaction['gain_loss']
    currency = transaction['currency']
    date = parser.parse(transaction['date'])
    amount = float(transaction['amount'])
    temp_amount_before = 0
    temp_amount_after = 0

    for item in data:
        temp_type = item['type']
        temp_currency = item['currency']
        temp_date = parser.parse(item['date'])
        temp_amount = float(item['amount'])

        if temp_currency == currency and temp_type == TYPE_BUY_STR:
            date_delta = date - datetime.timedelta(days=30)
            if temp_date > date_delta and temp_date < date:
                temp_amount_before += temp_amount

            date_delta = date + datetime.timedelta(days=30)
            if temp_date < date_delta and temp_date > date:
                temp_amount_after += temp_amount

    if amount <= temp_amount_before or amount <= temp_amount_after:
        gain_loss = 0

    return gain_loss


def check_loss_transaction(data):
    for item in data:
        type = item['type']
        gain_loss = float(item['gain_loss'])

        if type == TYPE_SELL_STR and gain_loss < 0:
            item['gain_loss'] = check_superficial_loss(item, data)

    return data


if __name__ == "cost_basis":
    merge_data()
    get_cost_basis()

    with open(config.CURRENCIES_FILE, 'w') as file:
        json.dump(variables, file)

    all_data = []

    for currency in variables:
        all_data += currency['list']

    all_data = sorted(all_data, key=lambda d: d['timestampms'])
    all_data = check_loss_transaction(all_data)
    all_data = add_totals(all_data)

    with open(config.DATA_FILE, 'w') as file:
        json.dump(all_data, file)