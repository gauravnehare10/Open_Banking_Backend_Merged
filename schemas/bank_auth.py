import requests
from urllib.parse import urlparse, parse_qs
from fastapi import HTTPException
from config.bank_data import BANK_FUNCTIONS
from config.database import account_access_consents, account_auth_tokens
import uuid

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


def process_redirect(redirect_uri):
    # Parse the URL fragment
    parsed_url = urlparse(redirect_uri)
    fragment = parsed_url.fragment  # The part after '#'

    # Parse the fragment into a dictionary
    params = parse_qs(fragment)

    # Extract the 'code' parameter
    code = params.get("code", [None])[0]  # Get the first value or None if not found

    if code:
        return code
    else:
        return {"error": "code parameter not found in redirectUri"}

def authorize(consent_id: str, bank_info):
    """
    Redirect user to authorize the consent.
    """
    auth_url = bank_info.get("AUTH_URL")
    
    request_data = {
        "client_id": bank_info.get("CLIENT_ID"),
        "response_type": "code id_token",
        "scope": "openid accounts",
        "redirect_uri": bank_info.get("REDIRECT_URI"),
        "request": consent_id,
        "authorization_mode": "AUTO_POSTMAN",
        "authorization_result": "APPROVED",
        "authorization_username": bank_info.get("AUTHORIZATION_USERNAME"),
        "authorization_accounts": "*"   
    }
    query_params = "&".join([f"{key}={value}" for key, value in request_data.items()])
    redirect_url = f"{auth_url}?{query_params}"
    response = requests.get(redirect_url)
    redirect_uri = response.json().get('redirectUri')
    code = process_redirect(redirect_uri)
    return code

def get_auth_consent(bank, userId):
    """
    Create an Account Access Consent.
    """
    BANK_FUNCTIONS[bank]
    
    bank_info = BANK_FUNCTIONS[bank]()
    url = f"{bank_info.get("API_BASE_URL")}/account-access-consents"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_access_token(bank_info)}"
    }
    payload = {
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
        "Risk": {}
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        consent_data = response.json()["Data"]
        consent_id = consent_data["ConsentId"]
        code = authorize(consent_id, bank_info)
        consent_data["_id"] = str(uuid.uuid4())
        consent_data["UserId"] = userId
        consent_data["bank"] = bank
        account_access_consents.insert_one(consent_data)
        return {"code": code, "consent_id": consent_id}
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create consent: {response.json()}"
        )


def get_bank_info(bank):
    if bank not in BANK_FUNCTIONS:
        raise HTTPException(status_code=400, detail="Invalid bank name")
    
    return BANK_FUNCTIONS[bank]()

def fetch_access_token(userId, bank):
    tokens = account_auth_tokens.find_one({'UserId': userId, 'bank': bank})
    return tokens.get("access_token")


def get_consent_id(userId, bank):
    consent = account_access_consents.find_one({'UserId': userId, 'bank': bank})
    consent_id = consent.get("ConsentId")
    return consent_id


def store_in_db(data, UserId, bank, collection_name):
    for one_data in data:
        one_data["_id"] = str(uuid.uuid4())
        one_data["UserId"] = UserId
        one_data["bank"] = bank
        collection_name.insert_one(one_data)