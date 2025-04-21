from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from app.core.cache import get_cache_info, clear_cache
from app.core.security import verify_token
import time
import random

router = APIRouter()

@router.get("/info", response_model=dict, summary="Informações do cache")
async def cache_info(current_user: str = Depends(verify_token)):
    """
    Retorna informações sobre o estado atual do cache.
    
    Este endpoint requer autenticação. O usuário precisa fornecer um token JWT válido.
    """
    return get_cache_info()

@router.post("/clear", response_model=dict, summary="Limpar cache")
async def clear_cache_endpoint(current_user: str = Depends(verify_token)):
    """
    Limpa todo o cache do sistema.
    
    Este endpoint requer autenticação. O usuário precisa fornecer um token JWT válido.
    """
    clear_cache()
    return {"message": "Cache limpo com sucesso"}

@router.get("/test", summary="Testar tempos de resposta com e sem cache")
async def test_cache_response_time(
    response: Response, 
    flush: bool = Query(False, description="Se True, ignora o cache e força uma nova consulta")
):
    """
    Endpoint para testar a diferença de tempo de resposta com e sem cache.
    
    Este endpoint simula um processamento demorado e demonstra a melhoria de desempenho com cache.
    Use o parâmetro `flush=true` para forçar uma nova consulta (ignorando o cache).
    """
    start_time = time.time()
    
    # Chave de cache simples para este endpoint
    cache_key = "cache_test_endpoint"
    
    # Simular processamento demorado (apenas quando não está usando cache ou com flush=true)
    if flush:
        # Processamento simulado (0.5 a 1.5 segundos)
        sleep_time = random.uniform(0.5, 1.5)
        time.sleep(sleep_time)
        response.headers["X-Cache-Status"] = "BYPASS"
    else:
        # Verificar se temos resposta em cache
        from app.core.cache import CACHE
        from datetime import datetime
        
        current_time = datetime.utcnow()
        if cache_key in CACHE:
            result, expiry_time = CACHE[cache_key]
            if current_time < expiry_time:
                response.headers["X-Cache-Status"] = "HIT"
                elapsed = time.time() - start_time
                return {
                    "message": "Resposta do cache",
                    "cache_status": "HIT",
                    "time_elapsed_ms": round(elapsed * 1000, 2),
                    "cached_at": result["timestamp"]
                }
        
        # Se não houver cache válido, executar o processamento
        sleep_time = random.uniform(0.5, 1.5)
        time.sleep(sleep_time)
        response.headers["X-Cache-Status"] = "MISS"
        
        # Armazenar no cache por 30 segundos
        from app.core.cache import CACHE
        from datetime import timedelta
        
        result = {
            "message": "Processamento realizado",
            "timestamp": time.time()
        }
        expiry_time = current_time + timedelta(seconds=30)
        CACHE[cache_key] = (result, expiry_time)
    
    elapsed = time.time() - start_time
    
    return {
        "message": "Teste de cache",
        "cache_status": response.headers["X-Cache-Status"],
        "time_elapsed_ms": round(elapsed * 1000, 2),
        "timestamp": time.time()
    }
