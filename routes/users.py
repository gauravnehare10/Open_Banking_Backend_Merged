from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException

from config.database import users_collection, account_auth_tokens, account_access_consents
from models.models import User
from schemas.user_auth import get_current_user


router = APIRouter(prefix="/users")

@router.get("/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user

@router.put('/{user_id}/update')
async def update_user(user_id: str, request: dict, current_user: User = Depends(get_current_user)):
    try:
        existing_user = await users_collection.find_one({'_id': user_id})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_fields = {key: value for key, value in request.items() if value is not None}
        update_result = await users_collection.update_one(
            {"_id": user_id},
            {"$set": updated_fields}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the user.")

        # Fetch the updated user details
        updated_user = await users_collection.find_one({"_id": user_id})        
        return {
            "message": "User details updated successfully.",
            "updated_user": updated_user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")