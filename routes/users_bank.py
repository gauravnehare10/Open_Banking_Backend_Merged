from typing import List
from fastapi import APIRouter, Depends, HTTPException

from models.models import User
from schemas.user_auth import get_current_user
from config.database import account_access_consents, account_auth_tokens, accounts, transactions, balances, beneficiaries
from schemas.bank_auth import check_bank_authorization, get_data
from pymongo import DESCENDING

router = APIRouter()


@router.get("/authorized-banks", response_model=List[str])
async def get_authorized_banks(current_user: User = Depends(get_current_user)):
    """Fetch all banks that the user has authorized (with approved consent)."""
    cursor = account_access_consents.find(
        {"UserId": current_user.userId, "Status": "Authorised"},
        {"bank": 1, "_id": 0}
    )
    authorized_banks = await cursor.to_list(length=None)
    banks = [bank["bank"] for bank in authorized_banks]
    
    if not banks:
        raise HTTPException(status_code=404, detail="No authorized banks found for this user")

    return banks

@router.get("/bank-accounts/{bank}")
async def get_bank_details(bank: str, current_user: User = Depends(get_current_user)):
    authorised = check_bank_authorization(current_user.userId, bank)
    
    accounts_data = await accounts.find(
        {"UserId": current_user.userId, "bank": bank}
    ).to_list(length=None)
    for data in accounts_data:
        data.pop("_id")
    
    return accounts_data

# @router.get('/balance-and-transaction/{bank}/{account_id}')
# async def get_balance_and_transaction(bank: str, account_id: str, current_user: User=Depends(get_current_user)):
#     authorized = await check_bank_authorization(current_user.userId, bank)
    
#     balance = await balances.find({"bank": bank, "UserId": current_user.userId, "AccountId": account_id}).to_list(length=None)
#     transaction = await transactions.find({"bank": bank, "UserId": current_user.userId, "AccountId": account_id}).to_list(length=None)
#     for one_balance in balance:
#         one_balance.pop("_id")
#     for one_transaction in transaction:
#         one_transaction.pop("_id")

#     transactions_and_balances = {
#         "balances": balance,
#         "transactions": transaction
#     }
#     return transactions_and_balances



@router.get('/balance-and-transaction/{bank}/{account_id}')
async def get_balance_and_transaction(
    bank: str,
    account_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        authorized = await check_bank_authorization(current_user.userId, bank)
    except HTTPException as e:
        raise e
    
    balance_cursor = balances.find({
        "bank": bank,
        "UserId": current_user.userId,
        "AccountId": account_id
    }).sort("DateTime", DESCENDING).limit(1)
    balance_list = await balance_cursor.to_list(length=1)
    
    transaction_cursor = transactions.find({
        "bank": bank,
        "UserId": current_user.userId,
        "AccountId": account_id
    }).sort("BookingDateTime", DESCENDING).limit(5)
    transaction_list = await transaction_cursor.to_list(length=5)
    
    if balance_list:
        for record in balance_list:
            record.pop("_id", None)
    for record in transaction_list:
        record.pop("_id", None)

    result = {
        "balance": balance_list[0] if balance_list else {},
        "transactions": transaction_list
    }
    
    return result

@router.get('/{bank}/accounts/{account_id}')
async def get_account_by_id(bank: str, account_id: str, current_user: User=Depends(get_current_user)):
    print(current_user.userId)
    try:
        authorized = await check_bank_authorization(current_user.userId, bank)
    except HTTPException as e:
        raise e
    
    account = await get_data(accounts, bank, current_user.userId, account_id)

    return account

@router.get('/{bank}/accounts/{account_id}/transactions')
async def get_transactions_by_acc_id(bank: str, account_id: str, current_user: User=Depends(get_current_user)):
    try:
        authorized = await check_bank_authorization(current_user.userId, bank)
    except HTTPException as e:
        raise e
    
    transactions_details = await get_data(transactions, bank, current_user.userId, account_id)

    return transactions_details

@router.get('/{bank}/accounts/{account_id}/beneficiaries')
async def get_beneficiaries_by_id(bank: str, account_id: str, current_user: User=Depends(get_current_user)):
    try:
        authorized = await check_bank_authorization(current_user.userId, bank)
    except HTTPException as e:
        raise e
    
    beneficiaries_data = await get_data(beneficiaries, bank, current_user.userId, account_id)

    return beneficiaries_data

    
