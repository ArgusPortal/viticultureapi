from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings

# Configurar o logger no nível do módulo
logger = logging.getLogger(__name__)

# Modificar o CryptContext para usar outros algoritmos também como fallback
pwd_context = CryptContext(
    schemes=["bcrypt", "sha256_crypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    sha256_crypt__default_rounds=100000
)

# Usar HTTPBearer como esquema principal para simplificar a interface
# Tornar auto_error=False para permitir tratamento customizado do erro
http_bearer = HTTPBearer(
    auto_error=False,
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
    
    # Se não recebeu credenciais, retorna erro imediatamente
    if not credentials:
        logger.error("Nenhum token de autenticação fornecido")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não autenticado"
        )
    
    try:
        # Remover a referência específica ao year=2022
        logger.info(f"Verificando token: {credentials.credentials[:10]}...")
        
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            logger.error("Token inválido: 'sub' ausente no payload")
            raise credentials_exception
            
        logger.info(f"Token válido para usuário: {username}")
        return str(username)
    except JWTError as e:
        logger.error(f"Erro ao verificar token JWT: {str(e)}")
        raise credentials_exception
    except Exception as e:
        # Adicionar captura genérica para registrar todos os erros possíveis
        logger.error(f"Erro não esperado na verificação do token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no processamento da autenticação: {str(e)}"
        )

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
