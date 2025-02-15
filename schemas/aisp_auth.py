import requests
from fastapi import HTTPException
from config.bank_data import BANK_FUNCTIONS
from config.database import account_access_consents, account_auth_tokens

def get_access_token(bank_info):
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": bank_info.get("CLIENT_ID"),
        "client_secret": bank_info.get("CLIENT_SECRET"),
        "scope": "accounts"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        response = requests.post(
            bank_info.get("TOKEN_URL"),
            data=payload,
            headers=headers
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get access token: {response.json()}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_access_token(userId, bank):
    tokens = await account_auth_tokens.find_one({'UserId': userId, 'bank': bank})
    return tokens.get("access_token")


async def get_consent_id(userId, bank):
    consent = await account_access_consents.find_one({'UserId': userId, 'bank': bank})
    consent_id = consent.get("ConsentId")
    return consent_id


async def upsert_data(collection, filter_query, update_data):
    await collection.update_one(filter_query, {"$set": update_data}, upsert=True)

async def check_bank_authorization(userId, bank):
    consent = await account_access_consents.find_one(
        {"UserId": userId, "bank": bank, "Status": "Authorised"}
    )

    if not consent:
        raise HTTPException(status_code=403, detail="Bank not Authorised")
    
    return consent

async def get_data(collection, bank, userId, account_id):
    data = await collection.find({'UserId': userId, 'bank': bank, "AccountId": account_id}).to_list(length=None)

    for one_data in data:
        one_data.pop("_id")
    return data