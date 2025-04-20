from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from passlib.context import CryptContext
import os

from app.core.security import create_access_token
from app.core.config import settings

# Configuração para verificação de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Carrega usuários do .env
def load_users_from_env():
    users = {}
    i = 1
    while True:
        username_key = f"USER{i}_USERNAME"
        password_key = f"USER{i}_PASSWORD"
        
        username = os.getenv(username_key)
        password = os.getenv(password_key)
        
        if not username or not password:
            break
            
        # Armazena o hash da senha se estiver em texto plano no .env
        # Em produção, já armazene os hashes no .env
        hashed_password = password
        if not password.startswith("$2"):  # Verifica se já é um hash bcrypt
            hashed_password = pwd_context.hash(password)
            
        users[username] = {
            "username": username,
            "hashed_password": hashed_password
        }
        
        i += 1
    
    return users

# Carrega usuários do .env ou usa o fake_users_db para desenvolvimento
users_db = load_users_from_env() or {
    "user@example.com": {
        "username": "user@example.com",
        "hashed_password": "$2b$12$RtIL8MmQqDWbXrQzboJJB.tBp9hNUXQMVEUlhY9pv7KAhQOQkRZXC",  # "password"
    }
}

router = APIRouter()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verifica se a senha está correta
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
