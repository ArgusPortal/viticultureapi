# Detalhamento Técnico: Arquivos da Pasta Raiz

Este documento fornece um detalhamento técnico dos arquivos principais localizados na pasta raiz da ViticultureAPI, explicando a função de cada componente e como eles se integram ao sistema.

## 1. Estrutura da Pasta Raiz

A pasta raiz do projeto contém arquivos essenciais para a configuração, execução e documentação da API:

```
/
├── main.py                # Ponto de entrada principal da aplicação
├── config.py              # Configurações globais da aplicação
├── requirements.txt       # Dependências do projeto
├── .env                   # Variáveis de ambiente (não versionado)
├── .env.example           # Exemplo de variáveis de ambiente
├── .gitignore             # Arquivos ignorados pelo git
├── README.md              # Documentação principal do projeto
├── LICENSE                # Informações de licenciamento
└── app/                   # Pasta principal da aplicação
```

## 2. Arquivos Principais

### 2.1. `main.py`

Este é o ponto de entrada principal da aplicação ViticultureAPI, responsável por inicializar e configurar o servidor FastAPI.

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import api_router
from app.core.config import settings
from app.core.security import get_current_user
from app.core.exceptions import setup_exception_handlers
from app.database.init_db import init_db
import uvicorn
import logging

# Configuração de logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup de rotas
app.include_router(api_router, prefix=settings.API_PREFIX)

# Setup de tratamento de exceções
setup_exception_handlers(app)

@app.on_event("startup")
async def startup_event():
    """Executa ações durante a inicialização do servidor"""
    logger.info("Inicializando servidor ViticultureAPI")
    await init_db()
    logger.info("Banco de dados inicializado")

@app.on_event("shutdown")
async def shutdown_event():
    """Executa ações durante o encerramento do servidor"""
    logger.info("Encerrando servidor ViticultureAPI")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
```

O arquivo `main.py` realiza várias funções críticas:

1. Inicializa a aplicação FastAPI com metadados e configurações
2. Configura middleware como CORS para permitir acesso pela API
3. Registra todas as rotas da API vindas do módulo de rotas
4. Configura tratamento de exceções para respostas de erro consistentes
5. Define eventos de inicialização e encerramento do servidor
6. Inicializa o banco de dados durante a inicialização
7. Configura o servidor uvicorn quando executado diretamente

### 2.2. `config.py`

Centraliza todas as configurações da aplicação, separando configurações de ambiente e padronizando acesso a variáveis.

```python
from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List, Optional, Dict, Any, Union
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Informações do projeto
    PROJECT_NAME: str = "ViticultureAPI"
    PROJECT_DESCRIPTION: str = "API para análise de dados da viticultura brasileira"
    VERSION: str = "0.1.0"
    
    # Ambiente
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT != "production"
    RELOAD: bool = ENVIRONMENT != "production"
    
    # Servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    API_PREFIX: str = "/api/v1"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/viticulture")
    TEST_DATABASE_URL: Optional[str] = os.getenv("TEST_DATABASE_URL")
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Storage
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # local, s3, azure
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./storage")
    
    # External APIs
    WINE_DATA_API_KEY: Optional[str] = os.getenv("WINE_DATA_API_KEY")
    WEATHER_API_KEY: Optional[str] = os.getenv("WEATHER_API_KEY")
    
    # Cache
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # Validações
    @validator("DATABASE_URL")
    def validate_database_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if not v:
            raise ValueError("DATABASE_URL must be provided")
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Instância única das configurações
settings = Settings()
```

Este arquivo permite:
1. Centralizar todas as configurações em um único local
2. Carregar configurações de variáveis de ambiente ou arquivos .env
3. Definir valores padrão para configurações não especificadas
4. Validar configurações críticas antes da inicialização
5. Usar tipagem estrita para evitar erros de configuração

### 2.3. `requirements.txt`

Lista todas as dependências necessárias para executar o projeto:

```
# Web framework
fastapi>=0.104.0
uvicorn>=0.23.2
pydantic>=2.4.2
pydantic-settings>=2.0.3
starlette>=0.27.0

# Processamento de Dados
pandas>=2.1.1
numpy>=1.26.0
matplotlib>=3.8.0
scikit-learn>=1.3.1

# Web Scraping e Requisições
requests>=2.31.0
beautifulsoup4>=4.12.2
urllib3>=2.0.7

# Autenticação e segurança
python-jose>=3.3.0
passlib>=1.7.4
python-multipart>=0.0.6
bcrypt>=4.0.1

# Utils
python-dotenv>=1.0.0
httpx>=0.25.0
tenacity>=8.2.3
loguru>=0.7.2

# Testing
pytest>=7.4.2
pytest-asyncio>=0.21.1
pytest-cov>=4.1.0

# Desenvolvimento
black>=23.9.1
isort>=5.12.0
mypy>=1.5.1
flake8>=6.1.0
types-requests>=2.31.0.2
types-python-jose>=3.3.4.8
```

## 3. Interação entre Arquivos Raiz e Componentes

A estrutura de arquivos na raiz foi projetada para facilitar:

1. **Configuração**: `config.py` e `.env` fornecem configuração centralizada acessível a todos os módulos
2. **Inicialização**: `main.py` é o ponto de entrada que conecta e configura todos os componentes
3. **Dependências**: `requirements.txt` garante consistência de ambiente
4. **Documentação**: `README.md` e outros arquivos servem como porta de entrada para novos desenvolvedores

## 4. Conclusão

Os arquivos na pasta raiz da ViticultureAPI estabelecem a fundação sobre a qual o resto da aplicação é construída. Eles garantem:

1. **Configurabilidade**: através de variáveis de ambiente e arquivos de configuração
2. **Manutenibilidade**: através de dependências bem definidas e ferramentas de qualidade
3. **Documentação**: através de documentação clara e estruturada

Esta arquitetura de raiz robusta permite que o desenvolvimento e implantação da aplicação aconteçam de forma suave e consistente, independentemente do ambiente ou da complexidade do sistema.
