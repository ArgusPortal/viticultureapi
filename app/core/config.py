import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "VitiBrasil API"
    
    # JWT Config
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sua_chave_secreta_aqui")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
settings = Settings()
