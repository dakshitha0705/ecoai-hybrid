# backend/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import LoginRequest, LoginResponse
from backend.auth.jwt_handler import authenticate_user, create_access_token
from backend.auth.roles import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"],
    }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
