"""Auth API — Stage 3: profile route token verification.

`/protected/profile` now actually verifies the bearer token by calling
`supabase.auth.get_user(token)`. Missing/invalid/expired/tampered tokens
return 401; a valid token returns 200 with the user's data.
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from supabase_client import SupabaseError, create_auth_backend

app = FastAPI(
    title="Auth API",
    description="Sign up, log in, log out and protected routes backed by Supabase Auth.",
    version="1.3.0",
)

AUTH = create_auth_backend()

bearer_scheme = HTTPBearer(auto_error=False)

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


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Extract the bearer token, or raise 401 if absent/malformed."""
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def protected_profile(token: str = Depends(get_bearer_token)):
    user = AUTH.get_user(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired or tampered token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user": user.to_dict()}



