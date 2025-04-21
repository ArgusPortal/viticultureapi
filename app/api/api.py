from fastapi import APIRouter

from app.api.endpoints import processing, exports, imports, production, commercialization, auth, cache

api_router = APIRouter()

# Adicionar routers com descrições mais claras
api_router.include_router(production.router, prefix="/production", tags=["Produção"])
api_router.include_router(processing.router, prefix="/processing", tags=["Processamento"])
api_router.include_router(imports.router, prefix="/imports", tags=["Importação"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exportação"])
api_router.include_router(commercialization.router, prefix="/commercialization", tags=["Comercialização"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(cache.router, prefix="/cache", tags=["Cache"])
