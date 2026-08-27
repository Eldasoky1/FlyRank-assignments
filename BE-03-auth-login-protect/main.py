"""Auth API — Stage 2: public route and unverified protected route.

Adds:
- GET /public/info        -> 200, no auth required
- GET /protected/profile  -> stub: only checks the Authorization header
  format (must be `Bearer <token>`); returns 401 if missing/invalid.
  Real token verification lands in the next stage.
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from supabase_client import SupabaseError, create_auth_backend

app = FastAPI(
    title="Auth API",
    description="Sign up, log in, log out and protected routes backed by Supabase Auth.",
    version="1.2.0",
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
    # Stage 2 stub: only the header format is checked. The token is NOT yet
    # verified against Supabase — real verification arrives in Stage 3.
    return {"stub": True, "note": "token format ok, verification coming next stage"}



