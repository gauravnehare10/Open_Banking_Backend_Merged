from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from models.models import User, TransferRequest
from schemas.user_auth import get_current_user
from config.bank_data import BANK_FUNCTIONS, get_bank_info
import httpx
from config.database import pisp_auth_tokens, pisp_payments_consents
import uuid
from schemas.pisp_auth import get_access_token, fetch_access_token, fetch_consent

router = APIRouter()


@router.post('/create-payment-consent')
async def create_payment_consent(bank: str, creditor_details: TransferRequest, current_user: User=Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")

    bank_info = get_bank_info(bank)
    idempotency_key = str(uuid.uuid4())
    access_token = await get_access_token(bank, current_user.userId)
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
            "CreditorAccount": {
                "SchemeName": creditor_details.schemeName,
                "Identification": creditor_details.identification,
                "Name": creditor_details.name,
                "SecondaryIdentification": creditor_details.secIdentif
            },
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
            "https://ob.sandbox.natwest.com/open-banking/v3.1/pisp/domestic-payment-consents",
            headers=headers,
            json=payload)
        if consent_response.status_code != 201:
            raise HTTPException(status_code=consent_response.status_code, detail=consent_response.text)
        
        consent_data = consent_response.json()["Data"]
        consent_data["UserId"] = current_user.userId
        consent_data["bank"] = bank
        consent_data["IdempotencyKey"] = idempotency_key
        await pisp_payments_consents.update_one({"UserId": current_user.userId, "bank": bank}, {"$set":consent_data}, upsert=True)
        consent_id = consent_data["ConsentId"]
        return consent_id

@router.get("/payment-authorize")
async def authorize_payment(bank: str, consent_id: str, current_user: User=Depends(get_current_user)):
    print(bank)
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")

    consent = await pisp_payments_consents.find_one({"UserId": current_user.userId, "bank": bank, "ConsentId": consent_id})
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


@router.post("/create_payment")
async def create_payment(bank: str, current_user: User=Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")
    bank_info = get_bank_info(bank)
    userId = current_user.userId
    access_token = await fetch_access_token(bank=bank, userId=userId)
    consent = await fetch_consent(bank, userId)
    url = f"{bank_info["API_BASE_URL"]}/domestic-payments"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-idempotency-key": consent["idempotency_key"],
        "x-jws-signature": "DUMMY_SIG"
    }
    data = {
        "Data": {
            "ConsentId": consent["consent_id"],
            "Initiation": {
                "InstructionIdentification": "instr-identification",
                "EndToEndIdentification": "e2e-identification",
                "InstructedAmount": {"Amount": "50.00", "Currency": "GBP"},
                "CreditorAccount": {
                    "SchemeName": "SortCodeAccountNumber",
                    "Identification": "50499910000998",
                    "Name": "ACME DIY",
                    "SecondaryIdentification": "secondary-identif"
                },
                "RemittanceInformation": {"Unstructured": "Tools", "Reference": "Tools"}
            }
        },
        "Risk": {"PaymentContextCode": "EcommerceGoods"}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)    
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()

@router.get("/get_payment_status/{payment_id}")
async def get_payment_status(bank: str, payment_id: str, current_user: User=Depends(get_current_user)):

    bank_info = get_bank_info(bank)
    access_token = await fetch_consent(bank=bank, userId=current_user.userId)
    url = f"{bank_info["API_BASE_URL"]}/domestic-payments/{payment_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()