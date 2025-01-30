from fastapi import APIRouter, Depends, HTTPException

from schemas.user_auth import get_current_user
from schemas.bank_auth import get_auth_consent, get_bank_info, fetch_access_token, get_consent_id
from models.models import User
from schemas.bank_auth import BANK_FUNCTIONS
from config.database import account_auth_tokens, account_access_consents
import uuid
import requests
import httpx

router = APIRouter(prefix="/banks")


# @router.post("/create-consent/")
# async def create_consent(bank_name: str, current_user: User = Depends(get_current_user)):
#     if bank_name not in BANK_FUNCTIONS:
#         raise HTTPException(status_code=404, detail="Bank not supported")
    
#     bank = BANK_FUNCTIONS[bank_name]()
    
#     # Step 1: Get the access token using client credentials
#     payload = {
#         "grant_type": "client_credentials",
#         "client_id": bank["CLIENT_ID"],
#         "client_secret": bank["CLIENT_SECRET"],
#         "scope": "accounts",
#     }

#     async with httpx.AsyncClient() as client:
#         response = await client.post(bank["TOKEN_URL"], data=payload)
#         if response.status_code != 200:
#             raise HTTPException(status_code=response.status_code, detail=response.text)
#         access_token = response.json().get("access_token")
#         print(access_token)

#     # Step 2: Create Account Access Consent with the access token
#     headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
#     consent_payload = {
#         "Data": {
#             "Permissions": [
#                 "ReadAccountsDetail",
#                 "ReadBalances",
#                 "ReadBeneficiariesDetail",
#                 "ReadDirectDebits",
#                 "ReadProducts",
#                 "ReadStandingOrdersDetail",
#                 "ReadTransactionsCredits",
#                 "ReadTransactionsDebits",
#                 "ReadTransactionsDetail",
#                 "ReadScheduledPaymentsBasic",
#                 "ReadScheduledPaymentsDetail",
#                 "ReadStatementsBasic", 
#                 "ReadStatementsDetail",
#                 "ReadOffers"
#             ]
#         },
#         "Risk": {},
#     }

#     async with httpx.AsyncClient() as client:
#         consent_response = await client.post(
#             f"{bank['API_BASE_URL']}/account-access-consents",
#             headers=headers,
#             json=consent_payload,
#         )
#         if consent_response.status_code != 201:
#             raise HTTPException(status_code=consent_response.status_code, detail=consent_response.text)

#         consent_data = consent_response.json()
#         consent_id = consent_data["Data"]["ConsentId"]
#         print(consent_id)

#     # Step 3: Redirect to the bank's authorization URL
#     auth_url = (
#         f"{bank['AUTH_URL']}?"
#         f"client_id={bank['CLIENT_ID']}&"
#         f"response_type=code id_token&"
#         f"scope=openid accounts&"
#         f"redirect_uri={bank['REDIRECT_URI']}&"
#         f"request={consent_id}"
#     )

#     return RedirectResponse(url=auth_url)


# @router.post("/exchange-token/")
# async def exchange_token(code: str, bank_name: str, current_user: User=Depends(get_current_user)):
#     if bank_name not in BANK_FUNCTIONS:
#         raise HTTPException(status_code=404, detail="Bank not supported")

#     bank = BANK_FUNCTIONS[bank_name]()
    
#     payload = {
#         "grant_type": "authorization_code",
#         "code": code,
#         "redirect_uri": bank["REDIRECT_URI"],
#         "client_id": bank["CLIENT_ID"],
#         "client_secret": bank["CLIENT_SECRET"],
#     }

#     async with httpx.AsyncClient() as client:
#         response = await client.post(bank["TOKEN_URL"], data=payload)
#         if response.status_code != 200:
#             raise HTTPException(status_code=response.status_code, detail=response.text)
        
#     return response.json()

########################################################################################
########################################################################################
########################################################################################

@router.get("/callback")
async def callback(bank: str, current_user: User=Depends(get_current_user)):
    """
    Handle callback after user authorization.
    """
    bank_info = get_bank_info(bank)
    consent = get_auth_consent(bank, current_user.userId)
    payload = {
        "client_id": bank_info.get("CLIENT_ID"),
        "client_secret": bank_info.get("CLIENT_SECRET"),
        "redirect_uri": bank_info.get("REDIRECT_URI"),
        "grant_type": "authorization_code",
        "code": consent["code"]
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(bank_info.get("TOKEN_URL"), data=payload, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        token_data["UserId"] = current_user.userId
        token_data["_id"] = str(uuid.uuid4())
        token_data["bank"] = bank
        account_auth_tokens.insert_one(token_data)
        access_token = token_data["access_token"]
        return access_token
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to get access token: {response.json()}"
        )
    
@router.get("/account-access-consent")
async def get_account_access_consent(bank, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    consent_id = get_consent_id(userId)
    url = f"{bank_info.get("API_BASE_URL")}/account-access-consents/{consent_id}"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]

        account_access_consents.update_one({"ConsentId": consent_id}, {"$set": data}, upsert=True)
        user_account_consent_data = account_access_consents.find_one({"ConsentId": consent_id})
        return user_account_consent_data