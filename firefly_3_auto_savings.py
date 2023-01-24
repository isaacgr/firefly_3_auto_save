import argparse
import json
import sys
import os
from requests import request

URL = 'http://localhost:8100/api/v1/transactions'
HEADERS = {
    'Accept': 'application/vnd.api+json'
}


def get_all_transactions(headers, page=1):
    response = request('GET', URL, headers=headers)
    print(response)
    response = response.json()
    if response['meta']['pagination']['current_page'] == response['meta']['pagination']['total_pages']:
        return response['data']
    return response.append(get_transactions_for_source_account(source_acct_name, headers, page=response['current_page']+1))

def get_transactions_for_source_account(source_acct_name, headers, page=1):
    pass

def get_transactions_for_destination_account(dest_acct_name, headers, page=1):
    pass

def create_auto_savings_transactions(source_transactions, apply=False):
    pass


def parse_commandline():
    parser = argparse.ArgumentParser(
        description='Create an (auto savings) transaction for each widthdrawal\
                        from source account to destination account of the specified amount', 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('transfer_amount', help='The amount to transfer from the source account to the destination account')
    parser.add_argument('source_account', help='The name of the source account to transfer from')
    parser.add_argument('destination_account', help='The name of the destination account to transfer to')
    parser.add_argument('--token', default='.firefly_api_token', help='Location of API token')
    parser.add_argument('--ignore-categories', nargs='+', help='Categories to ignore, i.e. "Credit Card"')
    parser.add_argument('--apply', action='store_true', help='Apply the transactions to the destination account')

    return parser.parse_args()


def main():
    options = parse_commandline()

    headers = HEADERS
    headers['Authorization'] = 'Bearer {}'.format(token)

    with open(options.token) as f:
        token = f.read().rstrip()

    source_acct_name = options.source_account
    dest_acct_name = options.destination_account

    transactions = get_all_transactions(headers)


if __name__ == '__main__':
    main()
