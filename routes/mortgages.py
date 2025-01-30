import uuid
from fastapi import APIRouter, HTTPException, Depends

from config.database import existing_mortgage_collection, new_mortgage_collection
from schemas.user_auth import get_current_user
from models.models import MortgageData, User

router = APIRouter(prefix="/mortgages")


@router.get('/')
async def get_mortgage_details(current_user: User = Depends(get_current_user)):
    try:
        existing_mortgages = existing_mortgage_collection.find({"user_id": current_user.userId})
        print(existing_mortgages)

        new_mortgages = new_mortgage_collection.find({"user_id": current_user.userId})
        print(new_mortgages)

        existing_mortgages_list = list(existing_mortgages)
        new_mortgages_list = list(new_mortgages)

        return {
            'existing_mortgages': existing_mortgages_list,
            'new_mortgages': new_mortgages_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/add_mortgage")
async def add_mortgage_details(data: MortgageData, current_user: User = Depends(get_current_user)):
    try:
        # Create the entry object with the data and the logged-in user's ID
        custom_id = str(uuid.uuid4())
        if data.hasMortgage:
            entry = {
                "_id": custom_id,
                "user_id": current_user.userId,  # Add the user ID to establish the relationship
                "hasMortgage": data.hasMortgage,
                "paymentMethod": data.paymentMethod,
                "estPropertyValue": data.estPropertyValue,
                "mortgageAmount": data.mortgageAmount,
                "loanToValue1": data.loanToValue1,
                "furtherAdvance": data.furtherAdvance,
                "mortgageType": data.mortgageType,
                "productRateType": data.productRateType,
                "renewalDate": data.renewalDate,
                "reference1": data.reference1,
            }

            # Save the entry in the existing_mortgage_details collection
            existing_mortgage_collection.insert_one(entry)
        else:
            entry = {
                "_id": custom_id,
                "user_id": current_user.userId,    # Add the user ID to establish the relationship
                "isLookingForMortgage": data.isLookingForMortgage,
                "foundProperty": data.foundProperty,
                "newMortgageType": data.newMortgageType,
                "depositAmount": data.depositAmount,
                "purchasePrice": data.purchasePrice,
                "loanToValue2": data.loanToValue2,
                "loanAmount": data.loanAmount,
                "sourceOfDeposit": data.sourceOfDeposit,
                "loanTerm": data.loanTerm,
                "newPaymentMethod": data.newPaymentMethod,
                'reference2': data.reference2
            }
            new_mortgage_collection.insert_one(entry)

        return {"message": "Mortgage details saved successfully."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    

@router.put('/{mortgage_id}/update_existing_mortgage')
async def update_existing_mortgage(mortgage_id: str, request: dict, current_user: User = Depends(get_current_user)):
    try:
        existing_mortgage = existing_mortgage_collection.find_one({"_id": mortgage_id, "user_id": current_user.userId})
        if not existing_mortgage:
            raise HTTPException(status_code=404, detail="Existing mortgage not found.")
        
        updated_fields = {key: value for key, value in request.items() if value is not None}
        update_result = existing_mortgage_collection.update_one(
            {"_id": mortgage_id, "user_id": current_user.userId},
            {"$set": updated_fields}
        )

        # Check if the update was successful
        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the mortgage.")
        
        # Fetch the updated existing mortgage details
        updated_mortgage = existing_mortgage_collection.find_one(
            {"_id": mortgage_id, "user_id": current_user.userId}
        )
        
        return {
            "message": "Existing mortgage updated successfully.",
            "updated_mortgage": updated_mortgage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@router.put("/{mortgage_id}/update_new_mortgage")
async def update_new_mortgage(mortgage_id: str, request: dict, current_user: User = Depends(get_current_user)):
    try:
        # Check if the new mortgage exists for the logged-in user
        new_mortgage = new_mortgage_collection.find_one(
            {"_id": mortgage_id, "user_id": current_user.userId}
        )
        if not new_mortgage:
            raise HTTPException(status_code=404, detail="New mortgage not found.")

        # Update the fields in the new mortgage
        updated_fields = {key: value for key, value in request.items() if value is not None}
        update_result = new_mortgage_collection.update_one(
            {"_id": mortgage_id, "user_id": current_user.userId},
            {"$set": updated_fields}
        )

        # Check if the update was successful
        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the mortgage.")

        # Fetch the updated new mortgage details
        updated_mortgage = new_mortgage_collection.find_one(
            {"_id": mortgage_id, "user_id": current_user.userId}
        )
        
        return {
            "message": "New mortgage updated successfully.",
            "updated_mortgage": updated_mortgage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
