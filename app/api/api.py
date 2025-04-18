from fastapi import APIRouter
from app.api.endpoints import production, processing, commercialization, imports, exports

api_router = APIRouter()

api_router.include_router(production.router, prefix="/production", tags=["Produção"])
api_router.include_router(processing.router, prefix="/processing", tags=["Processamento"])
api_router.include_router(commercialization.router, prefix="/commercialization", tags=["Comercialização"])
api_router.include_router(imports.router, prefix="/imports", tags=["Importação"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exportação"])
