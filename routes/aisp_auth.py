from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.user_auth import get_current_user
from schemas.aisp_auth import fetch_access_token
from models.models import User
from config.bank_data import BANK_FUNCTIONS, get_bank_info
from config.database import account_auth_tokens, account_access_consents
import httpx
from schemas.aisp_apis import *

router = APIRouter(prefix="/bank")


@router.post("/create-consent/")
async def create_consent(bank: str, current_user: User = Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")
    
    bank_info = get_bank_info(bank)
    
    # Step 1: Get the access token using client credentials
    payload = {
        "grant_type": "client_credentials",
        "client_id": bank_info["CLIENT_ID"],
        "client_secret": bank_info["CLIENT_SECRET"],
        "scope": "accounts",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(bank_info["TOKEN_URL"], data=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        token_data = response.json()
        token_data["UserId"] = current_user.userId
        token_data["bank"] = bank
        await account_auth_tokens.update_one({"UserId": current_user.userId, "bank": bank}, {"$set":token_data}, upsert=True)
        return {'message': 'Requested for consent'} 

@router.post('/submit-consent/')
async def create_account_access_consent(bank: str, current_user: User=Depends(get_current_user)):
    # Step 2: Create Account Access Consent with the access token
    access_token = await fetch_access_token(current_user.userId, bank)
    bank_info = get_bank_info(bank)
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    consent_payload = {
        "Data": {
            "Permissions": [
                "ReadAccountsDetail",
                "ReadBalances",
                "ReadBeneficiariesDetail",
                "ReadDirectDebits",
                "ReadProducts",
                "ReadStandingOrdersDetail",
                "ReadTransactionsCredits",
                "ReadTransactionsDebits",
                "ReadTransactionsDetail",
                "ReadScheduledPaymentsBasic",
                "ReadScheduledPaymentsDetail",
                "ReadStatementsBasic", 
                "ReadStatementsDetail",
                "ReadOffers"
            ]
        },
        "Risk": {},
    }

    async with httpx.AsyncClient() as client:
        consent_response = await client.post(
            f"{bank_info['API_BASE_URL']}/account-access-consents",
            headers=headers,
            json=consent_payload,
        )

        if consent_response.status_code != 201:
            raise HTTPException(status_code=consent_response.status_code, detail=consent_response.text)

        consent_data = consent_response.json()["Data"]
        consent_data["UserId"] = current_user.userId
        consent_data["bank"] = bank
        await account_access_consents.update_one({"UserId": current_user.userId, "bank": bank}, {"$set":consent_data}, upsert=True)
        consent_id = consent_data["ConsentId"]

    # Step 3: Redirect to the bank's authorization URL
    auth_url = (
        f"{bank_info['AUTH_URL']}?"
        f"client_id={bank_info['CLIENT_ID']}&"
        f"response_type=code id_token&"
        f"scope=openid accounts&"
        f"redirect_uri={bank_info['REDIRECT_URI']}&"
        f"request={consent_id}&"
        f"state=aisp"
    )

    return {"auth_url": auth_url}


@router.post("/exchange-token/")
async def exchange_token(
    code: str = Query(...), 
    bank: str = Query(...), 
    state: str = Query("aisp"), 
    current_user: User = Depends(get_current_user)
):
    userId = current_user.userId
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")

    bank_info = BANK_FUNCTIONS[bank]()
    
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": bank_info["REDIRECT_URI"],
        "client_id": bank_info["CLIENT_ID"],
        "client_secret": bank_info["CLIENT_SECRET"],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(bank_info["TOKEN_URL"], data=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        token_data = response.json()
        token_data["UserId"] = userId
        token_data["bank"] = bank
        token_data["state"] = state
        if state == "pisp":
            await pisp_auth_tokens.update_one({"UserId": userId, "bank": bank}, {"$set":token_data}, upsert=True)
        
        if state == "aisp":
            await account_auth_tokens.update_one({"UserId": userId, "bank": bank}, {"$set":token_data}, upsert=True)
            await get_account_access_consent(bank, userId)
            accounts_data = await get_accounts(bank, userId)
            for account in accounts_data:
                account_id = account["AccountId"]
                await get_account_transactions(account_id, bank, userId)
                await get_account_beneficiaries(account_id, bank, userId)
                await get_account_balances(account_id, bank, userId)
                await get_account_direct_debits(account_id, bank, userId)
                await get_account_standing_orders(account_id, bank, userId)
                await get_account_product(account_id, bank, userId)
                await get_account_scheduled_payments(account_id, bank, userId)
        
        
    return {"message": "Bank Authorisation Successful!"}


