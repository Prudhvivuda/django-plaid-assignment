# Assignment-Bright-Money

## Make and enter a virtaul env  

```sh
$ mkvirtualenv env
```
```sh
$ workon env
```  

## Install all dependencies

```sh
$ pip3 install -r requirements.txt
```

## Install RabbitMq (for Async Message Queue)

```sh
brew install rabbitmq
```

## Setup Models  

```sh
$ python3 manage.py makemigrations
```
```sh
$ python3 manage.py migrate 
```
```sh
$ python3 manage.py runserver
```
  
## Start Celery worker  

```sh
$ celery -A Plaid_Manager_API worker -l info
```
  
## API END-PONTS  
  
@http://localhost:8000/  
  
### Users API [ all POST req ]: (When hitting API with Postman make sure to include Authorization in Headers)  
  
-  users/register/  User-Register-API  
-  users/login/  User-Login-API  
-  users/logout/    User-Logout-API  
  
### Token_Exchange API  
  
[POST req]  

-  token_exchange/link_token/  Get-Plaid-Link_Token 
-  token_exchange/get_access_token/  Plaid-Link-Public_Token (exchange public_token with access_token)  
  
[GET req]  
  
-  token_exchange/home/    Get-Public_token 
-  token_exchange/get_items/	  Get-All-Items  
-  token_exchange/get_accounts/  Get-All-Accounts 
-  token_exchange/get_transactions/   Get-All-Transactions  
-  token_exchange/transaction_webhook/   Transaction-Webhook  


## Model Details:

### BankItemModel
  
-	bank_item_id
-	access_token
-	request_id
-	user  
  
### AccountModel
  
-	account_id
-	bank_item
-	balance_available
-	balance_current

### TransactionModel
  
-	transaction_id
-	account
-	amount
-	date
-	name
-	pending
  
### APILogModel

-	request_id
-	api_type
-	date_log
