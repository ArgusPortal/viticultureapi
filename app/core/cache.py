from datetime import datetime, timedelta
from functools import wraps
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

# Dicionário global para armazenar o cache
CACHE = {}

def cache_result(ttl_seconds=3600):  # Cache de 1 hora por padrão
    """
    Decorator para cachear resultados de funções.
    
    Args:
        ttl_seconds (int): Tempo de vida do cache em segundos
        
    Exemplo de uso:
        @cache_result(ttl_seconds=86400)  # 24 horas
        async def get_data():
            # código que busca dados...
            return data
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Criar uma chave única baseada na função e seus argumentos
            cache_key = f"{func.__module__}.{func.__name__}:{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            
            # Verificar se temos um cache válido
            current_time = datetime.utcnow()
            if cache_key in CACHE:
                result, expiry_time = CACHE[cache_key]
                if current_time < expiry_time:
                    logger.debug(f"Cache hit for {cache_key}")
                    return result
            
            # Se não houver cache válido, executar a função original
            result = await func(*args, **kwargs)
            
            # Armazenar o resultado no cache
            expiry_time = current_time + timedelta(seconds=ttl_seconds)
            CACHE[cache_key] = (result, expiry_time)
            logger.debug(f"Cache miss for {cache_key}, stored new result")
            
            return result
        return wrapper
    return decorator

def clear_cache():
    """Limpa todo o cache"""
    global CACHE
    CACHE = {}
    logger.info("Cache cleared")

def get_cache_info():
    """Retorna informações sobre o cache atual"""
    current_time = datetime.utcnow()
    cache_info = {
        "total_entries": len(CACHE),
        "valid_entries": sum(1 for _, expiry in CACHE.values() if current_time < expiry),
        "expired_entries": sum(1 for _, expiry in CACHE.values() if current_time >= expiry),
        "entries": [
            {
                "key": key,
                "expires_in": (expiry - current_time).total_seconds() if expiry > current_time else "expirado",
                "is_valid": expiry > current_time
            }
            for key, (_, expiry) in CACHE.items()
        ]
    }
    return cache_info

def add_cache_headers(response, max_age=3600):
    """
    Adiciona headers de cache HTTP à resposta.
    
    Args:
        response: Objeto Response do FastAPI
        max_age (int): Tempo máximo de cache em segundos
    """
    response.headers["Cache-Control"] = f"max-age={max_age}, public"
    expiry_time = (datetime.utcnow() + timedelta(seconds=max_age)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.headers["Expires"] = expiry_time
    
    # Gerar um ETag simples baseado no conteúdo da resposta
    if hasattr(response, "body") and response.body:
        etag = hashlib.md5(response.body).hexdigest()
        response.headers["ETag"] = f'"{etag}"'
