from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# Modificar o CryptContext para usar outros algoritmos também como fallback
pwd_context = CryptContext(
    schemes=["bcrypt", "sha256_crypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    sha256_crypt__default_rounds=100000
)

# Usar HTTPBearer como esquema principal para simplificar a interface
# Isso fará com que o Swagger UI mostre apenas um campo para o token
http_bearer = HTTPBearer(
    auto_error=True,
    description="Digite o token JWT recebido do endpoint /auth/token"
)

# Manter OAuth2PasswordBearer como referência, mas não usar no Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    # Cada token gerado tem um valor único devido ao timestamp e dados específicos
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Função principal para verificação de token usando HTTPBearer
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """Verifica o token de autenticação"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        return str(username)
    except JWTError:
        raise credentials_exception

# Função de fallback que usa OAuth2PasswordBearer (manter para compatibilidade)
def verify_oauth2_token(token: str = Depends(oauth2_scheme)):
    """Verificação de token usando OAuth2PasswordBearer (função legada)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        return str(username)
    except JWTError:
        raise credentials_exception
