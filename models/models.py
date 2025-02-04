from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    

class TokenData(BaseModel):
    username: str | None = None


class RegisterUser(BaseModel):
    username: str
    name: str | None = None
    email: str | None = None
    contactnumber: int | None = None
    password: str


class User(BaseModel):
    userId: str
    username: str
    name: str | None = None
    email: str | None = None
    contactnumber: int | None = None

class UserInDB(User):
    hashed_password: str
    
    
class UserUpdate(BaseModel):
    username: str
    name: str | None = None
    email: str | None = None
    contactnumber: int | None = None


class MortgageData(BaseModel):
    hasMortgage: bool
    paymentMethod: Optional[str] = None
    estPropertyValue: Optional[str] = None
    mortgageAmount: Optional[str] = None
    loanToValue1: Optional[str] = None
    furtherAdvance: Optional[str] = None
    mortgageType: Optional[str] = None
    productRateType: Optional[str] = None
    renewalDate: Optional[str] = None
    isLookingForMortgage: Optional[bool] = None
    newMortgageType: Optional[str] = None
    foundProperty: Optional[str] = None
    depositAmount: Optional[str] = None
    purchasePrice: Optional[str] = None
    loanToValue2: Optional[str] = None
    loanAmount: Optional[str] = None
    sourceOfDeposit: Optional[str] = None
    loanTerm: Optional[str] = None
    newPaymentMethod: Optional[str] = None
    reference1: Optional[str] = None
    reference2: Optional[str] = None

class BankDetailsResponse(BaseModel):
    bank: str
    UserId: str
    other_details: dict


class TransactionAndBalanceRes(BaseModel):
    bank: str
    UserId: str
    transaction: list[str]
    balance: list[str]
