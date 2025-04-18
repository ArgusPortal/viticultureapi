from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.core.security import create_access_token
from app.core.config import settings

# Usuários de exemplo (em produção, use banco de dados)
fake_users_db = {
    "user@example.com": {
        "username": "user@example.com",
        "hashed_password": "$2b$12$RtIL8MmQqDWbXrQzboJJB.tBp9hNUXQMVEUlhY9pv7KAhQOQkRZXC",  # "password"
    }
}

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Em produção, verifique a senha com pwd_context.verify()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
