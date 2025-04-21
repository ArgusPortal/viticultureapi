from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware que adiciona cabeçalhos de controle de cache às respostas HTTP.
    """
    
    def __init__(self, app, default_max_age=3600):
        super().__init__(app)
        self.default_max_age = default_max_age
        
    async def dispatch(self, request: Request, call_next):
        # Continuar com o processamento da requisição
        response = await call_next(request)
        
        # Só adicionar headers de cache para métodos GET
        if request.method == "GET":
            # Verificar se já existem headers de cache
            if "Cache-Control" not in response.headers:
                try:
                    # Adicionar headers básicos de cache
                    response.headers["Cache-Control"] = f"max-age={self.default_max_age}, public"
                    expiry_time = (datetime.utcnow() + timedelta(seconds=self.default_max_age)).strftime(
                        "%a, %d %b %Y %H:%M:%S GMT"
                    )
                    response.headers["Expires"] = expiry_time
                    
                    # Adicionar um ETag simples baseado no path da requisição
                    # (solução segura que não tenta acessar o corpo da resposta)
                    path_hash = hashlib.md5(f"{request.url.path}?{request.url.query}".encode()).hexdigest()
                    response.headers["ETag"] = f'W/"{path_hash}"'
                    
                    logger.debug(f"Cache headers added for {request.url.path}")
                except Exception as e:
                    logger.error(f"Error adding cache headers: {str(e)}")
                
        return response
