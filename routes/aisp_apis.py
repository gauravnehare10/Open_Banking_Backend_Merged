from fastapi import APIRouter, HTTPException, Depends

from schemas.bank_auth import fetch_access_token, get_bank_info, store_in_db
from schemas.user_auth import get_current_user
from config.database import *
import httpx
import uuid
from models.models import User

router = APIRouter()

@router.get("/accounts")
async def get_accounts(bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]["Account"]
        # Save to MongoDB
        store_in_db(data, userId, bank, accounts)

        return data
    
@router.get("/accounts/{account_id}")
async def get_account_details(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()

        return data


@router.get("/accounts/{account_id}/transactions")
async def get_account_transactions(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/transactions"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]["Transaction"]
        # Save to MongoDB
        store_in_db(data, userId, bank, transactions)
        
        return data
    
@router.get("/accounts/{account_id}/beneficiaries")
async def get_account_beneficiaries(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/beneficiaries"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]["Beneficiary"]
        # Save to MongoDB
        store_in_db(data, userId, bank, beneficiaries)

        return data

@router.get("/accounts/{account_id}/balances")
async def get_account_balances(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/balances"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]["Balance"]
        # Save to MongoDB
        store_in_db(data, userId, bank, balances)

        return data


@router.get("/accounts/{account_id}/direct-debits")
async def get_account_direct_debits(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/direct-debits"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]["DirectDebit"]
        # Save to MongoDB
        store_in_db(data, userId, bank, direct_debits)

        return data

@router.get("/accounts/{account_id}/standing-orders")
async def get_account_standing_orders(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/standing-orders"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]["StandingOrder"]
        # Save to MongoDB
        store_in_db(data, userId, bank, standing_orders)

        return data

@router.get("/accounts/{account_id}/product")
async def get_account_product(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/product"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]["Product"]
        # Save to MongoDB
        for product in data:
            product["_id"] = str(uuid.uuid4())
            product["UserId"] = userId
            products.insert_one(product)

        return data

@router.get("/accounts/{account_id}/scheduled-payments")
async def get_account_scheduled_payments(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/scheduled-payments"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()["Data"]["ScheduledPayment"]
        # Save to MongoDB
        for scheduled_payment in data:
            scheduled_payment["_id"] = str(uuid.uuid4())
            scheduled_payment["UserId"] = userId
            scheduled_payments.insert_one(scheduled_payment)

        return data

@router.get("/accounts/{account_id}/statements")
async def get_account_statements(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/statements"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        # Save to MongoDB

        return data

@router.get("/accounts/{account_id}/offers")
async def get_account_offers(account_id: str, bank: str, current_user: User=Depends(get_current_user)):
    userId = current_user.userId
    access_token = fetch_access_token(userId, bank)
    bank_info = get_bank_info(bank)
    url = f"{bank_info.get("API_BASE_URL")}/accounts/{account_id}/offers"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        # Save to MongoDB

        return data