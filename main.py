from fastapi import FastAPI
from routes import aisp_auth, user_auth, users, mortgages, users_bank, pisp_auth, fund_confirm_auth
from fastapi.middleware.cors import CORSMiddleware

from schemas import aisp_apis

app = FastAPI()

app.include_router(user_auth.router)
app.include_router(users.router)
app.include_router(mortgages.router)
app.include_router(aisp_auth.router)
app.include_router(aisp_apis.router)
app.include_router(users_bank.router)
app.include_router(pisp_auth.router)
app.include_router(fund_confirm_auth.router)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)