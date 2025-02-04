from fastapi import FastAPI
from routes import bank_auth, user_auth, users, mortgages, users_bank
from fastapi.middleware.cors import CORSMiddleware

from schemas import aisp_apis

app = FastAPI()

app.include_router(user_auth.router)
app.include_router(users.router)
app.include_router(mortgages.router)
app.include_router(bank_auth.router)
app.include_router(aisp_apis.router)
app.include_router(users_bank.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust the frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)