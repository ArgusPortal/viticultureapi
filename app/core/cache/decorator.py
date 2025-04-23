"""
Decorators para cache.

Fornece decorators para facilitar o uso de cache em funções e métodos.
"""
import logging
import inspect
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TypeVar, cast
from functools import wraps

from app.core.cache.factory import CacheFactory
from app.core.cache.interface import TaggedCacheProvider

logger = logging.getLogger(__name__)

# Definir tipo genérico para funções
F = TypeVar('F', bound=Callable[..., Any])

def cache_result(
    ttl_seconds: Optional[int] = 3600,
    key_prefix: Optional[str] = None,
    tags: Optional[List[str]] = None,
    provider: Optional[str] = None,
    include_args_in_key: bool = True,
    include_kwargs_in_key: bool = True,
    skip_args: Optional[List[int]] = None,
    skip_kwargs: Optional[List[str]] = None
) -> Callable[[F], F]:
    """
    Decorator para cache de resultados de funções.
    
    Args:
        ttl_seconds: Tempo de vida em segundos
        key_prefix: Prefixo para a chave de cache
        tags: Lista de tags a serem associadas à chave
        provider: Nome do provider de cache a ser usado
        include_args_in_key: Se True, inclui args na chave
        include_kwargs_in_key: Se True, inclui kwargs na chave
        skip_args: Lista de índices de args a serem ignorados na chave
        skip_kwargs: Lista de nomes de kwargs a serem ignorados na chave
        
    Returns:
        Função decorada
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Obter provider
            factory = CacheFactory.get_instance()
            cache_provider = factory.get_provider(provider)
            
            # Gerar chave de cache
            cache_key = _generate_cache_key(
                func, args, kwargs,
                prefix=key_prefix,
                include_args=include_args_in_key,
                include_kwargs=include_kwargs_in_key,
                skip_args=skip_args or [],
                skip_kwargs=skip_kwargs or []
            )
            
            # Verificar se resultado está em cache
            cached_result = await cache_provider.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Executar função
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Armazenar resultado em cache
            if tags and hasattr(cache_provider, "set_with_tags"):
                # Provedor suporta tags
                tagged_provider = cast(TaggedCacheProvider, cache_provider)
                await tagged_provider.set_with_tags(cache_key, result, tags, ttl_seconds)
            else:
                # Provedor não suporta tags ou sem tags para associar
                await cache_provider.set(cache_key, result, ttl_seconds)
            
            return result
        
        return cast(F, wrapper)
    
    return decorator

def _generate_cache_key(
    func: Callable,
    args: Tuple,
    kwargs: Dict[str, Any],
    prefix: Optional[str] = None,
    include_args: bool = True,
    include_kwargs: bool = True,
    skip_args: List[int] = [],
    skip_kwargs: List[str] = []
) -> str:
    """
    Gera uma chave de cache para uma função e seus argumentos.
    
    Args:
        func: Função
        args: Argumentos posicionais
        kwargs: Argumentos nomeados
        prefix: Prefixo para a chave
        include_args: Se True, inclui args na chave
        include_kwargs: Se True, inclui kwargs na chave
        skip_args: Lista de índices de args a serem ignorados
        skip_kwargs: Lista de nomes de kwargs a serem ignorados
        
    Returns:
        Chave de cache
    """
    # Iniciar com o nome da função
    key_parts = [prefix] if prefix else []
    key_parts.append(f"{func.__module__}.{func.__qualname__}")
    
    # Adicionar args se necessário
    if include_args:
        processed_args = []
        for i, arg in enumerate(args):
            if i in skip_args:
                continue
            try:
                # Tentar converter para string
                processed_args.append(str(arg))
            except Exception:
                # Se falhar, usar hash do repr
                processed_args.append(hashlib.md5(repr(arg).encode()).hexdigest())
        
        key_parts.append(":".join(processed_args))
    
    # Adicionar kwargs se necessário
    if include_kwargs:
        processed_kwargs = []
        for k, v in sorted(kwargs.items()):
            if k in skip_kwargs:
                continue
            try:
                # Tentar converter para string
                processed_kwargs.append(f"{k}={v}")
            except Exception:
                # Se falhar, usar hash do repr
                processed_kwargs.append(f"{k}={hashlib.md5(repr(v).encode()).hexdigest()}")
        
        key_parts.append(",".join(processed_kwargs))
    
    # Juntar tudo
    key = ":".join(key_parts)
    
    # Limitar tamanho da chave
    if len(key) > 250:
        # Se a chave for muito longa, usar hash
        return f"{key[:100]}:{hashlib.md5(key.encode()).hexdigest()}"
    
    return key

def invalidate_cache_tag(tag: str, provider: Optional[str] = None) -> Callable:
    """
    Decorator para invalidar cache com uma tag específica após a execução da função.
    
    Args:
        tag: Tag a ser invalidada
        provider: Nome do provider de cache a ser usado
        
    Returns:
        Função decorada
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Executar função
            result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Invalidar tag
            factory = CacheFactory.get_instance()
            cache_provider = factory.get_provider(provider)
            
            if hasattr(cache_provider, "invalidate_tag"):
                tagged_provider = cast(TaggedCacheProvider, cache_provider)
                count = await tagged_provider.invalidate_tag(tag)
                logger.info(f"Invalidated {count} cache entries with tag '{tag}'")
            else:
                logger.warning(f"Provider não suporta invalidação por tag: {tag}")
            
            return result
        
        return cast(F, wrapper)
    
    return decorator
