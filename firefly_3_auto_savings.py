import json
import sys
import os
import argparse
from datetime import datetime, timedelta
from requests import request

URL = 'http://localhost:8100/api/v1/transactions'
HEADERS = {
    'Accept': 'application/vnd.api+json'
}

VALID_TRANSACTION_TYPES=['withdrawal', 'withdrawals']
AUTOSAVE_DESCRIPTION='(auto-savings transfer)'
AUTOSAVE_CATEGORY='(auto-savings)'


def get_all_transactions(headers, page=1):
    response = request('GET', URL, headers=headers)
    response = response.json()
    if response['meta']['pagination']['current_page'] == response['meta']['pagination']['total_pages']:
        return response['data']
    return response.append(get_transactions_for_source_account(source_acct_name, headers, page=response['current_page']+1))


def filter_valid_transactions(source_acct, transactions, include_cash_transfer=False):
    valid_transactions = []
    for transaction in transactions:
        for transaction_split in transaction['attributes']['transactions']:
            if transaction_split['type'] in VALID_TRANSACTION_TYPES:
                if transaction_split['source_name'] == source_acct:
                    valid_transactions.append({
                            'currency_code': transaction_split['currency_code'],
                            'amount': transaction_split['amount'],
                            'description': transaction_split['description'],
                            'date': transaction_split['date']
                        })
            elif include_cash_transfer and transaction_split['type'] == 'transfer' and transaction_split['destination_name'] == 'Cash wallet':
                if transaction_split['source_name'] == source_acct:
                    valid_transactions.append({
                            'currency_code': transaction_split['currency_code'],
                            'amount': transaction_split['amount'],
                            'description': transaction_split['description'],
                            'date': transaction_split['date']
                        })

    return valid_transactions 


def create_auto_savings_transactions(valid_transactions, source_acct, dest_acct, amount, apply=False):
    # for each transaction on a given date, create a new transfer
    # of the 'amount' specified for the next business day
    current_date = datetime.now()
    date_to_transactions = {}

    for transaction in valid_transactions:
        transaction_date = datetime.strptime(transaction['date'].split('T')[0], '%Y-%m-%d')

        # if the transaction is on a weekend, it wont get processed until Monday
        # and so the auto save wont go out until a day after that
        if transaction_date.weekday() >= 5:
            transaction_date += timedelta(days=7-transaction_date.weekday())

        # if the auto save date is on a weekend, move it to the Monday
        auto_save_date = transaction_date + timedelta(days=1)
        if auto_save_date.weekday() >= 5:
            auto_save_date += timedelta(days=7-auto_save_date.weekday())

        date_to_transactions.setdefault(auto_save_date, [])
        date_to_transactions[auto_save_date].append(transaction)

    for date, transactions in date_to_transactions.items():
        total = amount * len(transactions)
        print('Creating auto-save transaction for {date}. Total savings transfer {total}. Source {source}. Dest {dest}. Includes {num_t} transactions.'\
                .format(date=date, source=source_acct, dest=dest_acct, num_t=len(transactions), total=total))
        

def parse_commandline():
    parser = argparse.ArgumentParser(
        description='Create an (auto-savings transfer) transaction of the specified amount for each widthdrawal \
                        from source account to destination account. \
                        This would mock something like the "simply savings" transfer that the \
                        Banks can setup everytime your debit card is used.', 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('transfer_amount', type=float, help='The amount to transfer from the source account to the destination account')
    parser.add_argument('source_account', help='The name of the source account to transfer from')
    parser.add_argument('destination_account', help='The name of the destination account to transfer to')
    parser.add_argument('--token', default='.firefly_api_token', help='Location of API token')
    parser.add_argument('--ignore-categories', nargs='+', help='Categories to ignore, i.e. "Credit Card"')
    parser.add_argument('--include-cash-transfer', action='store_true', default=False, 
            help='Some banks include widthdrawing cash as part of the simply savings transactions.\
                    If you have firefly setup to "transfer" into a cash wallet, this can get missed since its not a withdrawal.')
    parser.add_argument('--apply', action='store_true', default=False, help='Apply the transactions to the destination account')

    return parser.parse_args()


def main():
    options = parse_commandline()
    source_acct = options.source_account
    dest_acct = options.destination_account
    amount = options.transfer_amount

    with open(options.token) as f:
        token = f.read().rstrip()

    HEADERS['Authorization'] = 'Bearer {}'.format(token)

    transactions = get_all_transactions(HEADERS)
    valid_transactions = filter_valid_transactions(source_acct, transactions, include_cash_transfer=options.include_cash_transfer)

    create_auto_savings_transactions(valid_transactions, source_acct, dest_acct, amount, apply=options.apply)


if __name__ == '__main__':
    main()
