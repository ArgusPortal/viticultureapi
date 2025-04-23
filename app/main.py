"""
Ponto de entrada da aplicação FastAPI.

Define a configuração da API, rotas, middlewares e documentação.
"""
import sys
import os
from contextlib import asynccontextmanager

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Check if dependencies are installed
try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except ImportError:
    print("\n===== MISSING DEPENDENCIES =====")
    print("Some required packages are not installed. Please run:")
    print("pip install -r requirements.txt")
    print("\nIf requirements.txt is not available, run:")
    print("pip install fastapi uvicorn pandas requests beautifulsoup4 python-dotenv")
    print("\nFor data analysis and visualization capabilities, you may also want to install:")
    print("pip install matplotlib seaborn plotly numpy scipy statsmodels")
    print("\nFor advanced dashboarding, consider:")
    print("pip install dash streamlit")
    print("=====================================\n")
    sys.exit(1)

from app.api.api import api_router
from app.core.config import settings
from app.core.middleware import setup_middlewares
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import BaseAppException, handle_exception
import uvicorn

# Configurar logging
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "app.log"),
    log_json=os.getenv("LOG_JSON", "false").lower() == "true",
    app_name="viticultureapi"
)
logger = get_logger(__name__)

tags_metadata = [
    {
        "name": "Produção",
        "description": "Dados de produção de uvas, vinhos e derivados no Brasil.",
    },
    {
        "name": "Processamento",
        "description": "Dados de processamento industrial de uvas, separados por categoria (viníferas, americanas, etc.)."
    },
    {
        "name": "Importação",
        "description": "Estatísticas de importação de produtos vitivinícolas por tipo e país de origem."
    },
    {
        "name": "Exportação",
        "description": "Estatísticas de exportação de produtos vitivinícolas por tipo e país de destino."
    },
    {
        "name": "Comercialização",
        "description": "Dados de comercialização no mercado interno brasileiro."
    },
    {
        "name": "Autenticação",
        "description": "Endpoints para autenticação e gerenciamento de tokens."
    },
    {
        "name": "Cache",
        "description": "Endpoints para gerenciamento e monitoramento do sistema de cache."
    },
    {
        "name": "Diagnóstico",
        "description": "Endpoints para diagnóstico e monitoramento da aplicação."
    }
]

# Define lifespan context manager for app startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Store the original openapi method before overriding it
    original_openapi = app.openapi
    
    # Setup - runs on startup
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        # Call the original method instead of the custom one to avoid recursion
        openapi_schema = original_openapi()
        
        # Always force the OpenAPI version to a valid format (3.0.0)
        # This ensures compatibility with Swagger UI
        openapi_schema["openapi"] = "3.0.0"
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    logger.info("Aplicação iniciada: configurações carregadas e API pronta")
    
    yield  # This is where FastAPI runs and serves requests
    
    # Cleanup - runs on shutdown
    logger.info("Aplicação finalizada")

app = FastAPI(
    lifespan=lifespan,
    title="VitiBrasil API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",  # Usando a rota padrão /docs para o Swagger UI
    redoc_url="/redoc",
    openapi_version="3.0.0",
    description="""
# API para acesso aos dados de vitivinicultura da Embrapa
    
## Sobre o Projeto Acadêmico
    
Esta API foi desenvolvida como parte de um trabalho acadêmico para facilitar o acesso programático 
aos dados de vitivinicultura brasileira. O objetivo é disponibilizar informações estruturadas 
sobre a indústria vitivinícola nacional, permitindo análises e pesquisas mais eficientes.
    
## Funcionalidades
    
* **Produção**: Dados sobre produção de uvas, vinhos e derivados
* **Processamento**: Informações sobre processamento industrial de diferentes tipos de uvas
* **Comercialização**: Dados de mercado interno
* **Importação**: Estatísticas de importação por categoria (vinhos, espumantes, sucos, etc.)
* **Exportação**: Dados de exportação por categoria
    
## Fonte de Dados
    
Os dados são obtidos do site [VitiBrasil](http://vitibrasil.cnpuv.embrapa.br/) da Embrapa Uva e Vinho.
As informações são coletadas através de web scraping e armazenadas em formatos acessíveis via API REST.
    
## Metodologia
    
O projeto utiliza técnicas de web scraping para obter dados que anteriormente estavam disponíveis
apenas em formato HTML não-estruturado. Os desafios incluíram lidar com inconsistências na
formatação dos dados de origem e implementar mecanismos de fallback para garantir a disponibilidade
contínua das informações.
""",
    version="1.0.0",
    contact={
        "name": "Argus Portal",
        "email": "argusportal@gmail.com",
        "url": "https://github.com/ArgusPortal/viticultureapi",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    swagger_ui_parameters={
        "tagsSorter": "alpha",
        "operationsSorter": "method",
        "docExpansion": "none",
        "syntaxHighlight.theme": "monokai",
        "deepLinking": True,  # Melhora a navegação
        "defaultModelsExpandDepth": -1,  # Esconder modelos por padrão
        "defaultModelExpandDepth": 3,
        "displayRequestDuration": True,  # Mostra duração das requisições
        "filter": True,  # Habilita a busca
        "persistAuthorization": True,  # Manter autorização entre recarregamentos
        # Adicionar instruções específicas para autenticação
        "authDefinitions": {
            "securitySchemeDefinitions": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": """
### Como obter e usar o token:

1. Faça uma requisição POST para `/api/v1/auth/token` com:
   - Username: `admin@viticultureapi.com`
   - Password: `senha_admin_segura`

2. Copie o valor do campo `access_token` da resposta JSON

3. Cole o token no campo abaixo e clique em "Authorize"
                    """
                }
            }
        }
    },
    terms_of_service="http://example.com/terms/",
)

# Primeiro incluir rotas da API
app.include_router(api_router, prefix=settings.API_V1_STR)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar middlewares de logging, cache e tratamento de erros
setup_middlewares(app)

# Manipulador global de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Converter para exceção da aplicação
    app_exception = handle_exception(exc)
    
    # Registrar erro
    logger.error(
        f"Unhandled exception: {app_exception.message}",
        exc_info=True,
        path=request.url.path,
        method=request.method
    )
    
    # Retornar resposta JSON
    return JSONResponse(
        status_code=app_exception.status_code,
        content=app_exception.to_dict()
    )

# Endpoint para verificar schema OpenAPI
@app.get("/debug/openapi", include_in_schema=False)
async def debug_openapi():
    """Endpoint para verificar o schema OpenAPI diretamente"""
    schema = app.openapi()
    # Garantir que a versão OpenAPI está explicitamente definida
    if "openapi" not in schema:
        schema["openapi"] = "3.0.0"
    return schema

# Endpoint de verificação de saúde
@app.get("/health", tags=["Diagnóstico"], summary="Verificar saúde da API")
async def health_check():
    """
    Verifica se a API está funcionando corretamente.
    
    Returns:
        Dicionário com informações de saúde
    """
    from datetime import datetime
    import platform
    
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "version": app.version,
        "python_version": platform.python_version(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Modificar a rota raiz
@app.get("/", include_in_schema=False)
def root():
    return {"message": "Bem-vindo à API de dados vitivinícolas da Embrapa", "docs_url": "/docs"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)