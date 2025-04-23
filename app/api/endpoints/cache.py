"""
Endpoints para gerenciamento de cache.

Fornece endpoints para consultar, limpar e testar o sistema de cache.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any, List, Optional, cast
import time
import logging

from app.core.security import verify_token
from app.core.cache.factory import CacheFactory
from app.core.cache.interface import TaggedCacheProvider, CacheInfo

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/info", response_model=Dict[str, Any], summary="Informações do cache")
async def get_cache_info(
    provider: Optional[str] = Query(None, description="Provider específico para obter informações"),
    current_user: str = Depends(verify_token)
):
    """
    Obtém informações sobre o sistema de cache.
    
    Args:
        provider: Nome do provider específico ou None para todos
        
    Returns:
        Informações sobre o cache
    """
    factory = CacheFactory.get_instance()
    
    try:
        if provider:
            # Verificar se o provider existe
            if provider not in factory.get_available_providers():
                raise HTTPException(status_code=404, detail=f"Provider '{provider}' não encontrado")
            
            # Obter informações do provider específico
            cache_provider = factory.get_provider(provider)
            if hasattr(cache_provider, "get_info") and callable(getattr(cache_provider, "get_info")):
                # O método get_info é específico das implementações, não da interface base
                info = await getattr(cache_provider, "get_info")()
                return {"provider": provider, "info": info.to_dict()}
            else:
                return {"provider": provider, "info": {"details": "Provider não suporta informações detalhadas"}}
        else:
            # Obter informações de todos os providers
            providers_info = await factory.get_providers_info()
            return {
                "providers": providers_info,
                "available_providers": factory.get_available_providers(),
                "default_provider": factory._default_provider
            }
    except Exception as e:
        logger.error(f"Erro ao obter informações do cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações do cache: {str(e)}")

@router.post("/clear", response_model=Dict[str, Any], summary="Limpar cache")
async def clear_cache(
    provider: Optional[str] = Query(None, description="Provider específico para limpar"),
    tag: Optional[str] = Query(None, description="Tag específica para invalidar"),
    current_user: str = Depends(verify_token)
):
    """
    Limpa o cache.
    
    Args:
        provider: Nome do provider específico ou None para todos
        tag: Tag específica para invalidar ou None para limpar tudo
        
    Returns:
        Resultado da operação
    """
    factory = CacheFactory.get_instance()
    
    try:
        if provider:
            # Verificar se o provider existe
            if provider not in factory.get_available_providers():
                raise HTTPException(status_code=404, detail=f"Provider '{provider}' não encontrado")
            
            # Limpar provider específico
            cache_provider = factory.get_provider(provider)
            
            if tag and hasattr(cache_provider, "invalidate_tag"):
                # Invalidar tag específica
                # Cast explícito para TaggedCacheProvider
                tagged_provider = cast(TaggedCacheProvider, cache_provider)
                count = await tagged_provider.invalidate_tag(tag)
                return {
                    "message": f"Tag '{tag}' invalidada",
                    "provider": provider,
                    "invalidated_count": count
                }
            else:
                # Limpar todo o provider
                success = await cache_provider.clear()
                return {
                    "message": f"Cache '{provider}' limpo",
                    "success": success
                }
        else:
            # Limpar todos os providers
            results = {}
            for provider_name in factory.get_available_providers():
                cache_provider = factory.get_provider(provider_name)
                
                if tag and hasattr(cache_provider, "invalidate_tag"):
                    # Invalidar tag específica
                    # Cast explícito para TaggedCacheProvider
                    tagged_provider = cast(TaggedCacheProvider, cache_provider)
                    count = await tagged_provider.invalidate_tag(tag)
                    results[provider_name] = {
                        "invalidated_count": count,
                        "success": count > 0
                    }
                else:
                    # Limpar todo o provider
                    success = await cache_provider.clear()
                    results[provider_name] = {"success": success}
            
            return {
                "message": "Cache limpo" if not tag else f"Tag '{tag}' invalidada",
                "results": results
            }
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")

@router.get("/test", response_model=Dict[str, Any], summary="Testar desempenho do cache")
async def test_cache(
    provider: Optional[str] = Query(None, description="Provider específico para testar"),
    flush: bool = Query(False, description="Limpar cache antes do teste"),
    iterations: int = Query(5, description="Número de iterações para o teste"),
    current_user: str = Depends(verify_token)
):
    """
    Testa o desempenho do cache.
    
    Args:
        provider: Nome do provider específico ou None para usar o padrão
        flush: Se True, limpa o cache antes do teste
        iterations: Número de iterações para o teste
        
    Returns:
        Resultados do teste
    """
    factory = CacheFactory.get_instance()
    
    try:
        # Obter provider
        cache_provider = factory.get_provider(provider)
        provider_name = provider or factory._default_provider
        
        # Limpar cache se solicitado
        if flush:
            await cache_provider.clear()
        
        # Testar desempenho
        results = []
        key = "cache_test:" + str(time.time())
        value = {"test": "data", "timestamp": time.time()}
        
        # Teste de escrita
        start_time = time.time()
        for i in range(iterations):
            await cache_provider.set(f"{key}:{i}", value)
        write_time = time.time() - start_time
        
        # Teste de leitura (cache miss)
        start_time = time.time()
        for i in range(iterations):
            await cache_provider.get(f"cache_test:missing:{i}")
        read_miss_time = time.time() - start_time
        
        # Teste de leitura (cache hit)
        start_time = time.time()
        for i in range(iterations):
            await cache_provider.get(f"{key}:{i}")
        read_hit_time = time.time() - start_time
        
        # Teste de verificação de existência
        start_time = time.time()
        for i in range(iterations):
            await cache_provider.has(f"{key}:{i}")
        has_time = time.time() - start_time
        
        # Teste de TTL
        start_time = time.time()
        for i in range(iterations):
            await cache_provider.ttl(f"{key}:{i}")
        ttl_time = time.time() - start_time
        
        # Teste de exclusão
        start_time = time.time()
        for i in range(iterations):
            await cache_provider.delete(f"{key}:{i}")
        delete_time = time.time() - start_time
        
        return {
            "provider": provider_name,
            "iterations": iterations,
            "results": {
                "write_time": write_time,
                "write_time_per_op": write_time / iterations,
                "read_miss_time": read_miss_time,
                "read_miss_time_per_op": read_miss_time / iterations,
                "read_hit_time": read_hit_time,
                "read_hit_time_per_op": read_hit_time / iterations,
                "has_time": has_time,
                "has_time_per_op": has_time / iterations,
                "ttl_time": ttl_time,
                "ttl_time_per_op": ttl_time / iterations,
                "delete_time": delete_time,
                "delete_time_per_op": delete_time / iterations,
                "hit_vs_miss_ratio": read_miss_time / read_hit_time if read_hit_time > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Erro ao testar cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao testar cache: {str(e)}")
