"""Auth API — Stage 0: server set up and connected to Supabase.

This stage boots the FastAPI server and initialises the auth backend,
logging that everything is ready.
"""

from fastapi import FastAPI

from supabase_client import create_auth_backend

app = FastAPI(
    title="Auth API",
    description="Sign up, log in, log out and protected routes backed by Supabase Auth.",
    version="1.0.0",
)

AUTH = create_auth_backend()

print("Server running and connected to Supabase")


@app.get("/")
def root():
    return {"name": "Auth API", "status": "running"}
