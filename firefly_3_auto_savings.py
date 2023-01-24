import json
import sys
import os
import time
import argparse
from requests import request

URL = 'http://localhost:8100/api/v1/transactions'
HEADERS = {
    'Accept': 'application/vnd.api+json'
}

VALID_TRANSACTION_TYPES=['withdrawal', 'withdrawals']
AUTOSAVE_DESCRIPTION='(auto savings transfer)'
AUTOSAVE_CATEGORY='(auto savings)'


def get_all_transactions(headers, page=1):
    response = request('GET', URL, headers=headers)
    response = response.json()
    if response['meta']['pagination']['current_page'] == response['meta']['pagination']['total_pages']:
        return response['data']
    return response.append(get_transactions_for_source_account(source_acct_name, headers, page=response['current_page']+1))


def filter_valid_transactions(source_acct, transactions):
    valid_transactions = []
    for transaction in transactions:
        for transaction_split in transaction['attributes']['transactions']:
            if transaction_split['type'] in VALID_TRANSACTION_TYPES:
                if transaction_split['source_name'] == source_acct:
                    valid_transactions.append({
                            'currency_code': transaction_split['currency_code'],
                            'amount': transaction_split['amount'],
                            'description': transaction_split['description']
                        })
    return valid_transactions 


def create_auto_savings_transactions(valid_transactions, source_acct, dest_acct, amount, apply=False):
    # for each transaction on a given date, create a new transfer
    # of the 'amount' specified for the next business day
    pass


def parse_commandline():
    parser = argparse.ArgumentParser(
        description='Create an (auto savings transfer) transaction of the specified amount for each widthdrawal \
                        from source account to destination account. \
                        This would mock something like the "simply savings" transfer that the \
                        Banks can setup everytime your debit card is used.', 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('transfer_amount', help='The amount to transfer from the source account to the destination account')
    parser.add_argument('source_account', help='The name of the source account to transfer from')
    parser.add_argument('destination_account', help='The name of the destination account to transfer to')
    parser.add_argument('--token', default='.firefly_api_token', help='Location of API token')
    parser.add_argument('--ignore-categories', nargs='+', help='Categories to ignore, i.e. "Credit Card"')
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
    valid_transactions = filter_valid_transactions(source_acct, transactions)

    create_auto_savings_transactions(valid_transactions, source_acct, dest_acct, amount, apply=options.apply)


if __name__ == '__main__':
    main()
