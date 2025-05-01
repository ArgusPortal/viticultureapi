"""
Módulo de cache.

Fornece funcionalidades de cache para a aplicação.
"""

from functools import wraps
import hashlib
from datetime import datetime, timedelta
import logging
import asyncio

# Re-exportar classes e funções principais
from app.core.cache.interface import CacheProvider, TaggedCacheProvider, CacheInfo
from app.core.cache.factory import CacheFactory
from app.core.cache.memory_provider import MemoryCacheProvider
from app.core.cache.file_provider import FileCacheProvider
from app.core.cache.decorator import cache_result, invalidate_cache_tag  # Import from decorator.py instead

logger = logging.getLogger(__name__)

# Dicionário global para armazenar o cache (mantido para backward compatibility)
CACHE = {}

async def clear_cache():
    """Limpa todo o cache"""
    global CACHE
    CACHE = {}
    logger.info("Cache cleared")
    
    # Also clear cache in providers
    try:
        factory = CacheFactory.get_instance()
        for provider_name in factory.get_available_providers():
            provider = factory.get_provider(provider_name)
            if provider:
                await provider.clear()  # Added await here
    except Exception as e:
        logger.warning(f"Error clearing provider caches: {str(e)}")

def clear_cache_sync():
    """Versão síncrona de clear_cache para compatibilidade com código existente"""
    global CACHE
    CACHE = {}
    logger.info("Cache cleared (sync)")
    
    # For synchronous code that can't use await
    try:
        factory = CacheFactory.get_instance()
        for provider_name in factory.get_available_providers():
            provider = factory.get_provider(provider_name)
            if provider:
                # Try to use a synchronous method if available
                if hasattr(provider, 'clear_sync') and callable(getattr(provider, 'clear_sync')):
                    getattr(provider, 'clear_sync')()
                else:
                    # Run async clear in the event loop if available
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Schedule for later execution
                            asyncio.create_task(provider.clear())
                        else:
                            # Execute immediately
                            loop.run_until_complete(provider.clear())
                    except Exception as e:
                        logger.warning(f"Could not run async clear for provider {provider_name}: {str(e)}")
    except Exception as e:
        logger.warning(f"Error clearing provider caches synchronously: {str(e)}")

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
    """
    expiry_time = (datetime.utcnow() + timedelta(seconds=max_age)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.headers["Cache-Control"] = f"max-age={max_age}, public"
    response.headers["Expires"] = expiry_time
    
    # Gerar um ETag simples baseado no conteúdo da resposta
    if hasattr(response, "body") and response.body:
        etag = hashlib.md5(response.body).hexdigest()
        response.headers["ETag"] = f'"{etag}"'

# Exportar decorator de cache para compatibilidade com código existente
__all__ = [
    'CacheProvider',
    'TaggedCacheProvider',
    'CacheInfo',
    'CacheFactory',
    'MemoryCacheProvider',
    'FileCacheProvider',
    'cache_result',
    'invalidate_cache_tag',
    'clear_cache',
    'clear_cache_sync',
    'get_cache_info',
    'add_cache_headers',
    'CACHE'
]
