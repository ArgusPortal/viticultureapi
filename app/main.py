import sys
import os
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
    }
]

app = FastAPI(
    title="VitiBrasil API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
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
    
    ## Referências Bibliográficas
    
    - MELLO, L. M. R. de. Vitivinicultura brasileira: panorama 2019. Bento Gonçalves: Embrapa Uva e Vinho, 2020.
    - IBRAVIN. Panorama da vitivinicultura brasileira. Bento Gonçalves: IBRAVIN, 2022.
    """,
    version="1.0.0",
    contact={
        "name": "Seu Nome",
        "email": "seu.email@exemplo.com",
        "url": "https://github.com/seu-usuario/viticultureapi"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    swagger_ui_parameters={
        "tagsSorter": "alpha",
        "operationsSorter": "method",
        "docExpansion": "none"
    },
    terms_of_service="http://example.com/terms/",
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
