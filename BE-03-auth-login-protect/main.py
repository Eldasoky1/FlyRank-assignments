"""Auth API — Stage 5: Swagger UI documentation with bearer auth.

FastAPI serves `/docs` (Swagger UI) out of the box. Because the protected
routes depend on the `HTTPBearer` security scheme, Swagger shows a lock icon
on them and exposes an "Authorize" button. Test the flow by clicking
Authorize -> "Try it out" on any protected route.

To take the README screenshot, run the server and open /docs:
    uvicorn main:app --reload    →  http://localhost:8000/docs
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from supabase_client import SupabaseError, create_auth_backend

app = FastAPI(
    title="Auth API",
    description="Sign up, log in, log out and protected routes backed by Supabase Auth.",
    version="1.5.0",
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


def get_current_user(token: str = Depends(get_bearer_token)):
    """Reusable auth dependency. Verifies the bearer token via Supabase and
    returns the authenticated user, or raises 401 on invalid/expired/tampered."""
    user = AUTH.get_user(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired or tampered token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def protected_profile(user=Depends(get_current_user)):
    # The dependency already verified the token. Return the user's data.
    return {"user": user.to_dict()}


@app.get("/protected/dashboard")
def protected_dashboard(user=Depends(get_current_user)):
    # Same reusable auth dependency guards this route too.
    return {
        "user": user.to_dict(),
        "dashboard": {
            "greeting": f"Welcome back, {user.email}",
            "widgets": ["activity", "billing", "api-usage"],
        },
    }


@app.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user), token: str = Depends(get_bearer_token)):
    AUTH.logout(token)
    return None



