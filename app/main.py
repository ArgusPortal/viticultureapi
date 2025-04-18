import sys
import os
# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.api import api_router
from app.core.config import settings
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    description="""
    API para acesso aos dados de vitivinicultura da Embrapa.
    
    ## Funcionalidades
    
    * **Produção**: Dados sobre produção de uvas, vinhos e derivados
    * **Processamento**: Informações sobre processamento industrial
    * **Comercialização**: Dados de mercado interno
    * **Importação**: Estatísticas de importação
    * **Exportação**: Dados de exportação
    
    ## Fonte de Dados
    
    Os dados são obtidos do site [VitiBrasil](http://vitibrasil.cnpuv.embrapa.br/) da Embrapa.
    """,
    version="1.0.0",
    contact={
        "name": "Seu Nome",
        "email": "seu.email@exemplo.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde."}
    )

# Incluir rotas da API
app.include_router(api_router, prefix=settings.API_V1_STR)

# Rota raiz
@app.get("/")
def root():
    return {"message": "Bem-vindo à API de dados vitivinícolas da Embrapa"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
