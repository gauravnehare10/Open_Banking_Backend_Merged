from fastapi import APIRouter, HTTPException, Depends
from schemas.user_auth import get_current_user
from config.bank_data import BANK_FUNCTIONS, get_bank_info
from schemas.fund_confirm_auth import get_access_token, fetch_access_token, fetch_cof_consent
import httpx
from models.models import User, FundConfirmRequest
from config.database import cof_auth_tokens, cof_consents
import datetime


router = APIRouter(prefix="/cof")


@router.post('/create-consent')
async def create_cof_consent(bank: str, current_user: User=Depends(get_current_user)):
    print(bank)
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported.")
    userId = current_user.userId
    bank_info = get_bank_info(bank)
    access_token = await get_access_token(bank=bank, scope="fundsconfirmations")
    debtor_account = {
        "SchemeName": "UK.OBIE.SortCodeAccountNumber",
        "Identification": "50000012345602",
        "SecondaryIdentification": "Roll 56988"
    }
    expiration_time = "2025-03-30T00:11:10+00:00"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-fapi-financial-id": "0015800000jfwxXAAQ"
    }

    payload = {
        "Data": {
            "DebtorAccount": debtor_account,
            "ExpirationDateTime": expiration_time
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{bank_info["API_BASE_URL"]}/cbpii/funds-confirmation-consents",
            headers=headers, 
            json=payload)
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        consent_data = response.json()
        consent_data["UserId"] = userId
        consent_data["bank"] = bank
        await cof_consents.update_one({"UserId": userId, "bank": bank}, {"$set": consent_data}, upsert=True)
        return consent_data["Data"]["ConsentId"]
    
@router.get("/authorize-consent")
async def authorize_cof_consent(bank: str, current_user: User=Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported.")
    bank_info = get_bank_info(bank)
    userId = current_user.userId
    consent = await cof_consents.find_one({"UserId": userId, "bank": bank})

    auth_url =(
        f"{bank_info["AUTH_URL"]}"
        f"?client_id={bank_info["CLIENT_ID"]}"
        f"&response_type=code id_token"
        f"&scope=openid fundsconfirmations"
        f"&redirect_uri={bank_info["REDIRECT_URI"]}"
        f"&request={consent["Data"]["ConsentId"]}"
        f"&state=cof"
    )

    return auth_url

@router.get("/get-cof-consent")
async def get_cof_consent(bank:str, current_user: User=Depends(get_current_user)):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="Bank not supported")
    userId = current_user.userId
    bank_info = get_bank_info(bank)
    url = bank_info["API_BASE_URL"]
    access_token = await fetch_access_token(bank, userId)
    consent = await fetch_cof_consent(bank, userId)
    consent_id = consent["Data"]["ConsentId"]
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{url}/cbpii/funds-confirmation-consents/{consent_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            })
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        consent = response.json()
        await cof_consents.update_one({"Data.ConsentId": consent_id}, {"$set": consent}, upsert=True)
        return {"message": "Successfully Authorized!"}
    

'''==========================================================================================================='''


@router.get("/check-consent")
async def check_consent(bank: str, current_user: User=Depends(get_current_user)):
    print(bank)
    # Fetch the latest consent for the user and bank
    userId = current_user.userId
    consent = await fetch_cof_consent(bank, userId)

    if consent:
        status = consent["Data"]["Status"]
        consent_id = consent["Data"]["ConsentId"]
        expiration = datetime.datetime.fromisoformat(consent["Data"]["ExpirationDateTime"].replace("Z", ""))

        if expiration > datetime.datetime.utcnow():
            return {"valid": True, "status": status}

    return {"valid": False}


@router.post("/fund-confirmation")
async def fund_confirmation(bank: str, request: FundConfirmRequest, current_user: User=Depends(get_current_user)):
#async def fund_confirmation(bank: str, amount: float, userId: str): 
    bank_info = get_bank_info(bank)
    userId = current_user.userId
    consent = await fetch_cof_consent(bank, userId)
    if not consent:
        raise HTTPException(status_code=400, detail="No authorized consent found")

    consent_id = consent["Data"]["ConsentId"]
    print(consent_id)
    access_token = await fetch_access_token(bank, userId)
    print(access_token)

    url = f"{bank_info["API_BASE_URL"]}/cbpii/funds-confirmations"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-fapi-financial-id": "0015800000jfwxXAAQ",
        "Content-Type": "application/json"
    }
    payload = {
        "Data": {
            "ConsentId": consent_id,
            "Reference": "Purchase02",
            "InstructedAmount": {
                "Amount": f"{request.amount}",
                "Currency": "GBP"
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)