from fastapi import HTTPException

from config.bank_data import get_bank_info
from config.database import cof_auth_tokens, cof_consents
import httpx

async def fetch_access_token(bank, userId):
    token_data = await cof_auth_tokens.find_one({"UserId": userId, "bank": bank})
    return token_data["access_token"]

async def get_access_token(bank, scope):
    bank_info = get_bank_info(bank)
    payload = {
        "grant_type": "client_credentials",
        "client_id": bank_info["CLIENT_ID"],
        "client_secret": bank_info["CLIENT_SECRET"],
        "scope": scope 
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(bank_info["TOKEN_URL"], data=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        token_data = response.json()
        return token_data["access_token"]
    

async def fetch_cof_consent(bank: str, userId: str):
    consent = await cof_consents.find_one(
        {"bank": bank, "UserId": userId}
    )
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found.")
    return consent

