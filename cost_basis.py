import json

import config


TYPE_DEPOSIT_STR = "Deposit"
TYPE_WITHDRAWAL_STR = "Withdrawal"
TYPE_ADMIN_CREDIT_STR = "AdminCredit"
TYPE_BUY_STR = "Buy"
TYPE_SELL_STR = "Sell"
STATUS_COMPLETE_STR = "Complete"
STATUS_ADVANCED_STR = "Advanced"

total_gain_loss = 0
total_income = 0

buy_sell_profit = 0

variables = [
    {
        "currency": "BAT",
        "list": [],
        "quantity": 0,
        "cad_value": 0
    },
    {
        "currency": "BTC",
        "list": [],
        "quantity": 0,
        "cad_value": 0
    },
    {
        "currency": "ETH",
        "list": [],
        "quantity": 0,
        "cad_value": 0
    },
    {
        "currency": "SHIB",
        "list": [],
        "quantity": 0,
        "cad_value": 0
    },
    {
        "currency": "SLP",
        "list": [],
        "quantity": 0,
        "cad_value": 0
    },
    {
        "currency": "USD",
        "list": [],
        "quantity": 0,
        "cad_value": 0
    },
    {
        "currency": "ZEC",
        "list": [],
        "quantity": 0,
        "cad_value": 0
    }
]


# Merge content of transactions and transfers
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
    amount = item['amount']
    price = item['price']
    cad_value = item['cad_value']

    for temp_currency in variables:
        temp_fee_currency = temp_currency['currency']

        if fee_currency == temp_fee_currency:
            if type == TYPE_BUY_STR:
                temp_currency['quantity'] -= float(price) * float(amount)
                temp_currency['cad_value'] -= float(cad_value)
            elif type == TYPE_SELL_STR:
                temp_currency['quantity'] += float(price) * float(amount)
                temp_currency['cad_value'] += float(cad_value)


# Calculate the cost basis and gain/loss and save it to a file
def get_cost_basis():
    for currency in variables:
        list = currency['list']
        currency_quantity = currency['quantity']
        currency_cad_value = currency['cad_value']

        for item in list:
            type = item['type']
            amount = item['amount']
            cad_value = item['cad_value']
            fee_cad_value = item['fee_cad_value']
            item['total_buy_cad'] = 0
            item['total_sell_cad'] = 0

            if currency_quantity == 0:
                item['cost_basis'] = cad_value + fee_cad_value
            else:
                item['cost_basis'] = (currency_cad_value /
                                    currency_quantity) * float(amount)

            if type == TYPE_WITHDRAWAL_STR or type == TYPE_DEPOSIT_STR or type == TYPE_BUY_STR or type == TYPE_ADMIN_CREDIT_STR:
                item['cost_basis'] = 0
                gain_loss = 0

                if type != TYPE_WITHDRAWAL_STR:
                    currency_quantity += float(amount)
                    currency_cad_value += cad_value + fee_cad_value

                    if type == TYPE_DEPOSIT_STR:
                        global total_income
                        total_income += cad_value

                    if type == TYPE_BUY_STR:
                        set_other_currency(item)
                        item['total_buy_cad'] += cad_value

            elif type == TYPE_SELL_STR:
                currency_quantity -= float(amount)
                currency_cad_value - + cad_value + fee_cad_value
                set_other_currency(item)
                gain_loss = cad_value - float(item['cost_basis'])
                item['total_sell_cad'] += cad_value

            currency['quantity'] = currency_quantity
            currency['cad_value'] = currency_cad_value
            item['gain_loss'] = gain_loss
            
            global total_gain_loss
            total_gain_loss += gain_loss

    all_data = []

    for currency in variables:
        all_data += currency['list']

    all_data = sorted(all_data, key=lambda d: d['timestampms'])

    with open(config.DATA_FILE, 'w') as file:
        json.dump(all_data, file)


# Calculate buy and sell profit/loss
def get_buy_sell_profit():
    total_buy = 0
    total_sell = 0

    for currency in variables:
        list = currency['list']

        if list:
            last_item = list[-1]
            buy = last_item['total_buy_cad']
            sell = last_item['total_sell_cad']
            total_buy += buy
            total_sell += sell

    return total_sell - total_buy


if __name__ == "cost_basis":
    merge_data()
    get_cost_basis()
    buy_sell_profit = get_buy_sell_profit()