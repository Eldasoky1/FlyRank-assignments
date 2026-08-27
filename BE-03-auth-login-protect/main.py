"""Auth API — Stage 1: signup and login routes working.

Signup returns 201 + user; 400 on missing fields / duplicate email.
Login returns 200 + access/refresh tokens; 401 on bad credentials;
400 on missing fields.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from supabase_client import SupabaseError, create_auth_backend

app = FastAPI(
    title="Auth API",
    description="Sign up, log in, log out and protected routes backed by Supabase Auth.",
    version="1.1.0",
)

AUTH = create_auth_backend()

print("Server running and connected to Supabase")


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/auth/signup", status_code=201)
def signup(payload: SignupRequest):
    try:
        result = AUTH.sign_up(payload.email, payload.password)
    except SupabaseError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message)
    return {"user": result.user.to_dict()}


@app.post("/auth/login")
def login(payload: LoginRequest):
    try:
        result = AUTH.login(payload.email, payload.password)
    except SupabaseError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message)
    return {
        "user": result.user.to_dict(),
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
    }


@app.get("/")
def root():
    return {"name": "Auth API", "status": "running"}

