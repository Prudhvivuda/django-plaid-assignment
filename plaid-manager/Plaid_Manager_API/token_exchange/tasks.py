from __future__ import absolute_import, unicode_literals
from celery import shared_task
import datetime
import plaid
from token_exchange.models import AccountModel, BankItemModel, TransactionModel, APILogModel
from token_exchange.keys import PLAID_CLIENT_ID,PLAID_SECRET,PLAID_ENV


client = plaid.Client(client_id=PLAID_CLIENT_ID, secret=PLAID_SECRET,environment=PLAID_ENV)


@shared_task
def get_account(access_token_obj):

	access_token = access_token_obj['access_token']
	account_response = client.Accounts.get(access_token)

	api_log_obj = APILogModel.objects.create(
						request_id=account_response['request_id'], 
						api_type="get_accounts")
	api_log_obj.save()
	return account_response

@shared_task
def get_item(access_token_obj):

	access_token = access_token_obj['access_token']
	item_response = client.Items.get(access_token)

	api_log_obj = APILogModel.objects.create(
						request_id=item_response['request_id'], 
						api_type="get_items")
	api_log_obj.save()
	return item_response



@shared_task
def get_transactions(access_token=None, bank_item_id=None, new_transactions=500,days=30):
	if access_token is None:
		access_token = BankItemModel.objects.get(item_id=bank_item_id).access_token

	start_date = '{:%Y-%m-%d}'.format(
		datetime.datetime.now() + datetime.timedelta(-days))
	end_date = '{:%Y-%m-%d}'.format(datetime.datetime.now())

	transactions_response = client.Transactions.get(access_token, start_date, end_date,{'count': new_transactions,})

	api_log_obj = APILogModel.objects.create(
							request_id=transactions_response['request_id'],
							api_type="transaction_webhook_update")
	api_log_obj.save()

	if bank_item_id is None:
		bank_item_id = transactions_response['item']['item_id']
	bank_item = BankItemModel.objects.get(bank_item_id=bank_item_id)

	accounts = transactions_response['accounts']
	transactions = transactions_response['transactions']


	#accounts json objects from plaid
	for account in accounts:
		account_list = AccountModel.objects.filter(account_id=account['account_id'])

		#if accounts exist in db i.e 
		if account_list.count() > 0:
			for a in account_list:
				a.balance_available = account['balances']['available']
				a.balance_current = account['balances']['current']
				a.save()

		#account does not exists i.e DefaultUpdate
		else:
			account_obj = AccountModel.objects.create(
				bank_item=bank_item,
				account_id=account['account_id'],
				balance_available=account['balances']['available'],
				balance_current=account['balances']['current']
				)

			account_obj.save()

	transaction_list = TransactionModel.objects.filter(account__bank_item=bank_item).order_by('-date')
	i = 0
	for transaction in transactions:
		if transaction_list.count() > 0 and transaction['transaction_id'] == transaction_list[i].transaction_id:
			transaction_list[i].amount = transaction['amount']
			transaction_list[i].pending = transaction['pending']
			transaction_list[i].save()
			i+= 1

		else:
			account_ = AccountModel.objects.get(account_id=transaction['account_id'])

			transaction_obj = TransactionModel.objects.create(
				transaction_id=transaction['transaction_id'],
				account=account_,
				amount=transaction['amount'],
				date=transaction['date'],
				name=transaction['name'],
				pending=transaction['pending'])

			transaction_obj.save()

@shared_task
def delete_transactions(item_id, removed_transactions):

	for transaction in removed_transactions:
		TransactionModel.objects.filter(transaction_id=transaction).delete()