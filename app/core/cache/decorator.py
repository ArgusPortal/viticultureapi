"""
Decorators para cache.

Fornece decorators para facilitar o uso de cache em funções e métodos.
"""
import logging
import inspect
import hashlib
import json
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TypeVar, cast, overload
from functools import wraps
from datetime import datetime, timedelta

from app.core.cache.factory import CacheFactory
from app.core.cache.interface import TaggedCacheProvider

logger = logging.getLogger(__name__)

# Definir tipo genérico para funções
F = TypeVar('F', bound=Callable[..., Any])

# Overload para permitir uso como @cache_result e @cache_result()
@overload
def cache_result(ttl_seconds_or_func: F) -> F: ...

@overload
def cache_result(
    ttl_seconds_or_func: int = 3600,
    key_prefix: Optional[str] = None,
    tags: Optional[List[str]] = None,
    provider: Optional[str] = None,
    include_args_in_key: bool = True,
    include_kwargs_in_key: bool = True,
    skip_args: Optional[List[int]] = None,
    skip_kwargs: Optional[List[str]] = None,
    measure_time: bool = False,
    log_timing: bool = False
) -> Callable[[F], F]: ...

def cache_result(
    ttl_seconds_or_func: Union[int, F] = 3600,
    key_prefix: Optional[str] = None,
    tags: Optional[List[str]] = None,
    provider: Optional[str] = None,
    include_args_in_key: bool = True,
    include_kwargs_in_key: bool = True,
    skip_args: Optional[List[int]] = None,
    skip_kwargs: Optional[List[str]] = None,
    measure_time: bool = False,
    log_timing: bool = False
) -> Union[F, Callable[[F], F]]:
    """
    Decora uma função assíncrona para cachear seu resultado.
    
    Args:
        ttl_seconds_or_func: Tempo de vida do cache em segundos ou função que retorna o TTL
        key_prefix: Prefixo opcional para a chave do cache
        tags: Tags para categorizar o cache (opcional)
        provider: Nome do provider de cache (opcional)
        include_args_in_key: Se deve incluir args na chave do cache
        include_kwargs_in_key: Se deve incluir kwargs na chave do cache
        skip_args: Lista de índices de args a serem ignorados na chave
        skip_kwargs: Lista de nomes de kwargs a serem ignorados na chave
        measure_time: Se True, mede o tempo de execução da função
        log_timing: Se True, registra os tempos de execução no log
        
    Returns:
        Função decorada ou decorator
    """
    # Compatibilidade com chamadas diretas como @cache_result
    if callable(ttl_seconds_or_func) and not isinstance(ttl_seconds_or_func, int):
        return _cache_decorator(ttl_seconds_or_func, 3600, key_prefix, tags, provider, 
                              include_args_in_key, include_kwargs_in_key, 
                              skip_args, skip_kwargs, measure_time, log_timing)
    
    # Caso normal, com parâmetros: @cache_result(ttl_seconds=xxx)
    ttl_seconds = ttl_seconds_or_func if isinstance(ttl_seconds_or_func, int) else 3600
    
    def decorator(func: F) -> F:
        return _cache_decorator(func, ttl_seconds, key_prefix, tags, provider,
                               include_args_in_key, include_kwargs_in_key, 
                               skip_args, skip_kwargs, measure_time, log_timing)
    
    return decorator

def _cache_decorator(
    func: F,
    ttl_seconds: int,
    key_prefix: Optional[str],
    tags: Optional[List[str]],
    provider: Optional[str],
    include_args_in_key: bool,
    include_kwargs_in_key: bool,
    skip_args: Optional[List[int]],
    skip_kwargs: Optional[List[str]],
    measure_time: bool,
    log_timing: bool
) -> F:
    """Implementação real do decorator de cache"""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Obter provider - try/except para garantir que erros no cache não afetem a função original
        try:
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
            
            # Medir tempo de execução se solicitado
            start_time = time.time() if measure_time else None
            
            result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Calcular e registrar tempo se solicitado
            if start_time is not None:
                execution_time = time.time() - start_time
                if log_timing:
                    logger.info(f"Function {func.__name__} executed in {execution_time:.4f}s")
                # Adicionar informações de timing ao resultado se for um dicionário
                if isinstance(result, dict) and measure_time:
                    result['execution_time_seconds'] = execution_time
            
            # Armazenar resultado em cache
            if tags and hasattr(cache_provider, "set_with_tags"):
                # Provedor suporta tags
                tagged_provider = cast(TaggedCacheProvider, cache_provider)
                await tagged_provider.set_with_tags(cache_key, result, tags, ttl_seconds)
            else:
                # Provedor não suporta tags ou sem tags para associar
                await cache_provider.set(cache_key, result, ttl_seconds)
            
            # COMPATIBILITY WITH OLD IMPLEMENTATION
            # Also store in the global CACHE dict for backward compatibility
            try:
                from app.core.cache import CACHE
                # Ensure ttl_seconds is not None before using it
                seconds_value = ttl_seconds if ttl_seconds is not None else 3600
                expiry_time = datetime.utcnow() + timedelta(seconds=float(seconds_value))
                CACHE[cache_key] = (result, expiry_time)
            except ImportError:
                pass
            
            return result
        except Exception as e:
            # Em caso de erro no cache, executamos a função original
            logger.error(f"Error using cache for {func.__name__}: {str(e)}")
            
            # Ainda medir o tempo se solicitado, mesmo em caso de erro
            if measure_time:
                start_time = time.time()
                
            result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
            
            if measure_time:
                # Ensure start_time is defined and not None before using it
                execution_time = time.time() - start_time  # type: ignore
                if log_timing:
                    logger.info(f"Function {func.__name__} executed in {execution_time:.4f}s (cache error)")
                # Adicionar informações de timing ao resultado se for um dicionário
                if isinstance(result, dict):
                    result['execution_time_seconds'] = execution_time
            
            return result
    
    return cast(F, wrapper)

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
        
        if processed_args:
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
        
        if processed_kwargs:
            key_parts.append(",".join(processed_kwargs))
    
    # Juntar tudo
    key = ":".join([p for p in key_parts if p])
    
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
            try:
                factory = CacheFactory.get_instance()
                cache_provider = factory.get_provider(provider)
                
                if hasattr(cache_provider, "invalidate_tag"):
                    tagged_provider = cast(TaggedCacheProvider, cache_provider)
                    count = await tagged_provider.invalidate_tag(tag)
                    logger.info(f"Invalidated {count} cache entries with tag '{tag}'")
                else:
                    logger.warning(f"Provider não suporta invalidação por tag: {tag}")
            except Exception as e:
                logger.error(f"Error invalidating cache tag {tag}: {str(e)}")
            
            return result
        
        return cast(F, wrapper)
    
    return decorator
