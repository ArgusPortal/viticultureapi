"""
Módulo de cache.

Fornece funcionalidades de cache para a aplicação.
"""

# Re-exportar classes e funções principais
from app.core.cache.interface import CacheProvider, TaggedCacheProvider, CacheInfo
from app.core.cache.factory import CacheFactory
from app.core.cache.memory_provider import MemoryCacheProvider
from app.core.cache.file_provider import FileCacheProvider
from app.core.cache.decorator import cache_result, invalidate_cache_tag

# Exportar decorator de cache para compatibilidade com código existente
__all__ = [
    'CacheProvider',
    'TaggedCacheProvider',
    'CacheInfo',
    'CacheFactory',
    'MemoryCacheProvider',
    'FileCacheProvider',
    'cache_result',
    'invalidate_cache_tag'
]
