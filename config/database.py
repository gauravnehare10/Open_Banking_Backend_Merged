import os
from dotenv import find_dotenv, load_dotenv
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

MONGO_URL = os.getenv('MONGO_URL')

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

db_client = AsyncIOMotorClient(MONGO_URL)

db = db_client.Open_Banking

users_collection = db.user_details
existing_mortgage_collection = db.existing_mortgage_details
new_mortgage_collection = db.new_mortgage_details

account_access_consents = db.account_access_consents
account_auth_tokens = db.account_auth_tokens
accounts = db.accounts
transactions = db.transactions
beneficiaries = db.beneficiaries
balances =  db.balances
direct_debits = db.direct_debits
standing_orders = db.standing_orders
products = db.products
scheduled_payments = db.scheduled_payments
statements = db.statements
offers = db.offers

pisp_auth_tokens = db.pisp_auth_tokens
pisp_payments_consents = db.pisp_payments_consents

cof_auth_tokens = db.cof_auth_tokens
cof_consents = db.cof_consents