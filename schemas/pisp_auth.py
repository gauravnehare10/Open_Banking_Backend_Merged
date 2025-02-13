from config.database import pisp_auth_tokens, pisp_payments_consents
from fastapi import HTTPException
import httpx
from config.bank_data import BANK_FUNCTIONS, get_bank_info


async def fetch_access_token(bank, userId):
    tokens = await pisp_auth_tokens.find_one({'UserId': userId, 'bank': bank})
    return tokens.get("access_token")

async def get_access_token(bank, userId):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")
    
    bank_info = get_bank_info(bank)
    payload = {
        "grant_type": "client_credentials",
        "client_id": bank_info["CLIENT_ID"],
        "client_secret": bank_info["CLIENT_SECRET"],
        "scope": "payments" 
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(bank_info["TOKEN_URL"], data=payload)
        if response.status_code !=200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        token_data = response.json()
        token_data["UserId"] = userId
        token_data["bank"] = bank

        await pisp_auth_tokens.update_one({"UserId": userId, "bank": bank}, {"$set":token_data}, upsert=True)
        return token_data["access_token"]
    

async def fetch_consent(bank, userId):
    consent = await pisp_payments_consents.find_one({"UserId": userId, "bank": bank})
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found.")
    return consent
