from django.shortcuts import render

from django.views.decorators.csrf import csrf_protect,csrf_exempt
from django.http import JsonResponse, HttpResponse

from rest_framework.response import Response
from rest_framework import status,pagination
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated

import plaid
import json,datetime

from token_exchange.serializers import AccessTokenSerializer
from token_exchange.models import BankItemModel,APILogModel
from token_exchange.tasks import delete_transactions, get_transactions
from token_exchange.keys import PLAID_CLIENT_ID,PLAID_SECRET,PLAID_ENV

client = plaid.Client(client_id=PLAID_CLIENT_ID, secret=PLAID_SECRET, environment=PLAID_ENV)

class getLinkToken(APIView):

	'''
	[To get Link Token from Plaid Front End]
	@/plaid/link_token/
	[POST req : is sent with user credentials (id and secret) to  link/token/create]
	'''
	# permission_classes = [IsAuthenticated]

	def post(self,request):

		user = request.user
		if user.is_authenticated:
			configs = {
				'user': {
					'client_user_id': PLAID_CLIENT_ID
					},
				'products': ['auth', 'transactions'],
				'client_name': "Plaid Test App",
				'country_codes': ['US'],
				'language': 'en',
				'webhook': "https://webhook.site/c3c00dbc-0b03-46dc-a98e-13918a4f4e37",
				'link_customization_name': 'default',
				'account_filters': {
					'depository': {
						'account_subtypes': ['checking', 'savings'],
					},
				},
			}
			response = client.LinkToken.create(configs)
			api_log_obj = APILogModel.objects.create(
											request_id = response['request_id'], 
											api_type = "get_link_token")
			api_log_obj.save()
			return Response(data = response, status = status.HTTP_200_OK)
		return Response({"error": "User not Authenticated"}, status = status.HTTP_404_NOT_FOUND)


@csrf_protect
def home(request):
	'''
	@/plaid/home/
	'''
	return render(request, "linkToPublic.html",{})


class getAccessToken(APIView):
	'''
	@/plaid/get_access_token/
	[POST req : temp public token is exchanged with a permanent access token and saved in the db.]
	Transaction and Account are populated @Async
	Message Queue : Rabbitmq must have a worker running
	'''
	def post(self,request):

		request_data = request.POST
		public_token = request_data.get('public_token')
		try:
			exchange_response = client.Item.public_token.exchange(public_token)
			serializer = AccessTokenSerializer(data=exchange_response)
			if serializer.is_valid():
				access_token = serializer.validated_data['access_token']
				bank_item = BankItemModel.objects.create(access_token=access_token,
											bank_item_id=serializer.validated_data['item_id'],
											request_id=serializer.validated_data['request_id'],
											user=self.request.user)
				bank_item.save()
				api_log_obj = APILogModel.objects.create(
											request_id = serializer.validated_data['request_id'], 
											api_type = "get_access_token")
				api_log_obj.save()
				get_transactions.delay(access_token)
		except plaid.errors.PlaidError as e:
			return Response(status=status.HTTP_400_BAD_REQUEST)
		return Response(data = exchange_response, status = status.HTTP_200_OK)


class getItems(APIView):
	'''
	@/plaid/get_items/
	[GET req : fetches all items of user currently logged-in/request.user
	'''
	pagination.PageNumberPagination.page_size = 10

	def get(self,request):
		bank_item = BankItemModel.objects.filter(user=self.request.user)
		if len(bank_item)>0:
			try:
				access_token_obj_list = bank_item.values('access_token')
				items_responses = []
				for access_token_obj in access_token_obj_list:
					access_token = access_token_obj['access_token']
					item_response = client.Item.get(access_token)
					items_responses.append(item_response['item'])
					api_log_obj = APILogModel.objects.create(
											request_id=item_response['request_id'], 
											api_type="get_items")
					api_log_obj.save()
			except plaid.errors.PlaidError as e:
				return Response(status=status.HTTP_400_BAD_REQUEST)
			return Response(data={'items_list': items_responses}, status = status.HTTP_200_OK)
		else:
			return Response(status=status.HTTP_401_UNAUTHORIZED)


class getAccounts(APIView):

	'''
	@/plaid/get_accounts/
	[GET req : fetches all accounts from all items of user currently logged-in/request.user
	'''
	pagination.PageNumberPagination.page_size = 10

	def get(self,request):
		bank_item = BankItemModel.objects.filter(user = self.request.user)
		if len(bank_item)>0:
			try:
				access_token_obj_list = bank_item.values('access_token')
				accounts_responses = []
				for access_token_obj in access_token_obj_list:
					access_token = access_token_obj['access_token']
					# account_response=get_account.delay(access_token_obj)
					account_response = client.Accounts.get(access_token)
					accounts_responses.append(account_response['accounts'])
					api_log_obj = APILogModel.objects.create(
											request_id=account_response['request_id'], 
											api_type="get_accounts")
					api_log_obj.save()
			except plaid.errors.PlaidError as e:
				return Response(status=status.HTTP_400_BAD_REQUEST)
			return Response(data = {'accounts_list': accounts_responses}, status = status.HTTP_200_OK)
		else:
			return Response(status=status.HTTP_401_UNAUTHORIZED)




class getTransactions(APIView):

	'''
	[To fetch all Transactions of user]
	@/plaid/get_items/
	[GET req : fetches all transactions in all accounts of all items of user 
	currently logged-in/request.user and displays in json in a list format]
	'''

	# permission_classes  =  [IsAuthenticated]
	pagination.PageNumberPagination.page_size = 10

	def get(self,request):
		bank_item = BankItemModel.objects.filter(user=self.request.user)
		if len(bank_item)>0:
			try:
				access_token_obj_list = bank_item.values('access_token')
				transactions_responses=[]
				# transactions of 1 month i.e. 30 days
				start_date = '{:%Y-%m-%d}'.format(
					datetime.datetime.now() + datetime.timedelta(-30))
				end_date = '{:%Y-%m-%d}'.format(datetime.datetime.now())

				for access_token_obj in access_token_obj_list:
					access_token = access_token_obj['access_token']
					transaction_response = client.Transactions.get(access_token,start_date,end_date)
					transactions_responses.append(transaction_response['transactions'])

					api_log_obj = APILogModel.objects.create(
											request_id=transaction_response['request_id'], 
											api_type="get_transactions")
					api_log_obj.save()
				
			except plaid.errors.PlaidError as e:
				return Response(status=status.HTTP_400_BAD_REQUEST)
			return Response(data={'transactions_list': transactions_responses}, status=status.HTTP_200_OK)
		else:
			return Response(status=status.HTTP_401_UNAUTHORIZED)

@csrf_exempt
def transactionWebhook(request):
	'''[GET req : Webhook to listen to Transaction updates]
	@plaid/transaction_webhook/
	Message Queue : Rabbitmq must have a worker running
	'''
	
	request_data = request.POST
	webhook_type = request_data.get('webhook_type')
	webhook_code = request_data.get('webhook_code')


	if webhook_type == 'TRANSACTIONS':
		item_id = request_data.get('item_id')
		
		if webhook_code == 'TRANSACTIONS_REMOVED':
			removed_transactions = request_data.get('removed_transactions')
			delete_transactions.delay(item_id, removed_transactions)

		else:
			new_transactions = request_data.get('new_transactions')
			get_transactions.delay(None, item_id, new_transactions)

	return HttpResponse('Webhook received', status=status.HTTP_200_OK)

