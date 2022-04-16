import json
from dateutil import parser
import datetime

import config
import utils


TYPE_DEPOSIT_STR = "Deposit"
TYPE_WITHDRAWAL_STR = "Withdrawal"
TYPE_ADMIN_CREDIT_STR = "AdminCredit"
TYPE_BUY_STR = "Buy"
TYPE_BUY_OTHER_STR = "Buy_other"
TYPE_SELL_STR = "Sell"
TYPE_SELL_OTHER_STR = "Sell_other"
STATUS_COMPLETE_STR = "Complete"
STATUS_ADVANCED_STR = "Advanced"

total_gain_loss = 0
total_income = 0

total_buy_cad = 0
total_sell_cad = 0

buy_sell_profit = 0

variables = []


balances = utils.get_balances()

with open (config.BALANCES_FILE, 'w') as file:
    json.dump(balances, file)

for balance in balances:
    currency = balance['currency']

    if currency == "USD":
        currency_type = "fiat"
    else:
        currency_type = "crypto"
        
    variables.append({
        "currency": currency,
        "type": currency_type,
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
    try:
        with open(config.TRANSACTIONS_FILE, 'r') as file:
            transactions = json.load(file)
    except:
        utils.get_transactions()

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

    try:
        with open(config.TRANSFERS_FILE, 'r') as file:
            transfers = json.load(file)
    except:
        utils.get_transfers()

        with open(config.TRANSFERS_FILE, 'r') as file:
            transfers = json.load(file)

    for transfer in transfers:
        transfer_type = transfer['type']
        status = transfer['status']

        transfer.pop("status")
        transfer.pop("eid")
        transfer.pop("date_iso")

        if transfer_type == TYPE_DEPOSIT_STR or transfer_type == TYPE_WITHDRAWAL_STR:
            transfer.pop("destination")

            if transfer_type == TYPE_DEPOSIT_STR and status == STATUS_COMPLETE_STR:
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


def set_other_currencies():
    other_currencies = []

    for currency in variables:
        list = currency['list']

        for item in list:
            item_type = item['type']

            if item_type == TYPE_BUY_STR or item_type == TYPE_SELL_STR:
                temp_item = item.copy()
                temp_item['type'] = item_type + "_other"
                other_currencies.append(temp_item)

    for other_transaction in other_currencies:
        for currency in variables:
            currency_name = currency['currency']
            list = currency['list']
            final_list = list.copy()

            other_currency_name = other_transaction['fee_currency']
            other_timestampms = other_transaction['timestampms']
            if other_currency_name == currency_name:
                if list:
                    for item in list:
                        timestampms = item['timestampms']
                        index = final_list.index(item)

                        if other_timestampms >= timestampms:
                            final_list.insert(index + 1, other_transaction)
                            break;
                else:
                    final_list.append(other_transaction)
            currency['list'] = final_list
    
    return variables
    

def get_cost_basis():
    variables = set_other_currencies()

    for currency in variables:
        list = currency['list']
        currency_quantity = float(currency['quantity'])
        currency_cad_value = float(currency['cad_value'])
        total_sell_currency = 0

        for item in list:
            item_type = item['type']
            amount = float(item['amount'])
            cad_value = item['cad_value']
            usd_value = item['usd_value']
            fee_cad_value = item['fee_cad_value']
            item['total_buy_cad'] = 0
            item['total_sell_cad'] = 0
            item['total_buy_usd'] = 0
            item['total_sell_usd'] = 0

            if "price" in item:
                price = float(item['price'])

            if item_type == TYPE_WITHDRAWAL_STR or item_type == TYPE_DEPOSIT_STR or item_type == TYPE_BUY_STR or item_type == TYPE_SELL_OTHER_STR or item_type == TYPE_ADMIN_CREDIT_STR:
                item['cost_basis'] = 0
                gain_loss = 0

                if item_type != TYPE_WITHDRAWAL_STR:
                    currency_cad_value += cad_value + fee_cad_value

                    if item_type != TYPE_SELL_OTHER_STR:
                        currency_quantity += amount

                        if item_type == TYPE_BUY_STR:
                            currency['cad_value_buy'] += cad_value
                            currency['usd_value_buy'] += usd_value
                            currency['quantity_buy'] += amount
                    else:
                        currency_quantity += amount * price

            else:
                if item_type == TYPE_SELL_STR:
                    item['cost_basis'] = (currency_cad_value / currency_quantity) * amount
                    gain_loss = cad_value - float(item['cost_basis'])
                    total_sell_currency += amount
                    currency['quantity_sell'] += amount
                    currency['cad_value_sell'] += cad_value
                    currency['usd_value_sell'] += usd_value
                else:
                    item['cost_basis'] = 0

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
        item_type = item['type']
        cad_value = item['cad_value']
        gain_loss = item['gain_loss']

        if item_type == TYPE_DEPOSIT_STR or item_type == TYPE_ADMIN_CREDIT_STR:
            total_income += cad_value
        elif item_type == TYPE_BUY_STR:
            total_buy_cad += cad_value
        elif item_type == TYPE_SELL_STR:
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

        if temp_currency == currency and (temp_type == TYPE_BUY_STR or temp_type == TYPE_DEPOSIT_STR):
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
        item_type = item['type']
        gain_loss = float(item['gain_loss'])

        if item_type == TYPE_SELL_STR and gain_loss < 0:
            item['gain_loss'] = check_superficial_loss(item, data)

    return data


if __name__ == "cost_basis":
    merge_data()
    get_cost_basis()

    with open(config.CURRENCIES_FILE, 'w') as file:
        json.dump(variables, file)

    all_data = []

    for currency in variables:
        list = currency['list']
        final_list = list.copy()

        for item in list:
            type = item['type']
            
            if type == TYPE_BUY_OTHER_STR or type == TYPE_SELL_OTHER_STR:
                final_list.remove(item)

        all_data += final_list

    all_data = sorted(all_data, key=lambda d: d['timestampms'])
    all_data = check_loss_transaction(all_data)
    all_data = add_totals(all_data)

    with open(config.DATA_FILE, 'w') as file:
        json.dump(all_data, file)