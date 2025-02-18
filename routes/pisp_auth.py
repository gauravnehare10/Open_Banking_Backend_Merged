from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from models.models import User, TransferRequest
from schemas.user_auth import get_current_user
from config.bank_data import BANK_FUNCTIONS, get_bank_info
import httpx
from config.database import pisp_auth_tokens, pisp_payments_consents
import uuid
from schemas.pisp_auth import get_access_token, fetch_access_token, fetch_consent
from schemas.aisp_apis import get_accounts, get_account_balances, get_account_transactions

router = APIRouter()


@router.post('/create-payment-consent')
async def create_payment_consent(bank: str, creditor_details: TransferRequest, current_user: User=Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")

    bank_info = get_bank_info(bank)
    idempotency_key = str(uuid.uuid4())
    access_token = await get_access_token(bank, current_user.userId)
    creditor_account = {
                "SchemeName": creditor_details.schemeName,
                "Identification": creditor_details.identification,
                "Name": creditor_details.name,
                "SecondaryIdentification": creditor_details.secIdentif
            }
    payload = {
        "Data": {
            "Initiation": {
            "InstructionIdentification": "instr-identification",
            "EndToEndIdentification": "e2e-identification",
            "InstructedAmount": {
                "Amount": creditor_details.amount,
                "Currency": "GBP"
            },
            "DebtorAccount": None,
            "CreditorAccount": creditor_account,
            "RemittanceInformation": {
                "Unstructured": "Tools",
                "Reference": "Tools"
            }
            }
        },
        "Risk": {
            "PaymentContextCode": "EcommerceGoods",
            "MerchantCategoryCode": None,
            "MerchantCustomerIdentification": None,
            "DeliveryAddress": None
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-jws-signature": "DUMMY_SIG",
        "x-idempotency-key": idempotency_key 
        }

    async with httpx.AsyncClient() as client:
        consent_response = await client.post(
            f"{bank_info["API_BASE_URL"]}/pisp/domestic-payment-consents",
            headers=headers,
            json=payload)
        if consent_response.status_code != 201:
            raise HTTPException(status_code=consent_response.status_code, detail=consent_response.text)
        
        consent_data = consent_response.json()
        consent_data["UserId"] = current_user.userId
        consent_data["bank"] = bank
        consent_data["IdempotencyKey"] = idempotency_key
        await pisp_payments_consents.update_one({"UserId": current_user.userId, "bank": bank}, {"$set":consent_data}, upsert=True)
        consent_id = consent_data["Data"]["ConsentId"]
        return consent_id

@router.get("/payment-authorize")
async def authorize_payment(bank: str, consent_id: str, current_user: User=Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")

    consent = await pisp_payments_consents.find_one({"UserId": current_user.userId, "bank": bank})
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    bank_info = get_bank_info(bank)
    auth_url =(
        f"{bank_info["AUTH_URL"]}"
        f"?client_id={bank_info["CLIENT_ID"]}"
        f"&response_type=code id_token"
        f"&scope=openid payments"
        f"&redirect_uri={bank_info["REDIRECT_URI"]}"
        f"&request={consent_id}"
        f"&state=pisp"
    )

    return auth_url

@router.get("/create-payment-order")
async def create_payment(bank: str, current_user: User=Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")
    bank_info = get_bank_info(bank)
    userId = current_user.userId
    access_token = await fetch_access_token(bank, userId)
    consent_data = await fetch_consent(bank, userId)
    idempotency_key = consent_data["IdempotencyKey"]
    consent = consent_data["Data"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-jws-signature": "DUMMY_SIG",
        "x-idempotency-key": idempotency_key
    }
    request_data = {
        "Data": {
            "ConsentId": consent["ConsentId"],
            "Initiation": consent["Initiation"],
        },
        "Risk": consent_data["Risk"]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{bank_info["API_BASE_URL"]}/pisp/domestic-payments",  
            json=request_data, 
            headers=headers)
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        new_consent_data = response.json()
        new_consent_data["UserId"] = userId
        new_consent_data["bank"] = bank
        await pisp_payments_consents.update_one({"UserId": userId, "bank": bank}, {"$set":new_consent_data}, upsert=True)
        accounts_data = await get_accounts(bank, userId)
        for account in accounts_data:
            account_id = account["AccountId"]
            await get_account_transactions(account_id, bank, userId)
            await get_account_balances(account_id, bank, userId)
            print(account_id)

    return new_consent_data

@router.get("/get-payment-status")
async def get_payment_status(bank: str, payment_id: str, current_user: User=Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not suppported")
    bank_info = get_bank_info(bank)
    userId = current_user.userId
    access_token = await fetch_access_token(bank=bank, userId=userId)
    url = f"{bank_info["API_BASE_URL"]}/pisp/domestic-payments/{payment_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json())
        new_consent_data = response.json()
        new_consent_data["UserId"] = userId
        new_consent_data["bank"] = bank
        await pisp_payments_consents.update_one({"UserId": userId, "bank": bank}, {"$set":new_consent_data}, upsert=True)
    
    return response.json()