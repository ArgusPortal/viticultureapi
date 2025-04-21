import sys
import os
import pytest
import asyncio
from datetime import datetime, timedelta
import time

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Agora podemos importar dos módulos da aplicação
from app.core.cache import cache_result, clear_cache, get_cache_info, CACHE

# Contador para verificar quantas vezes a função real foi chamada
call_counter = 0

# Função de teste que será decorada com cache
@cache_result(ttl_seconds=10)  # Cache por 10 segundos para teste
async def sample_function(param1, param2=None):
    """Função de exemplo que simula uma operação demorada e incrementa o contador"""
    global call_counter
    call_counter += 1
    await asyncio.sleep(0.1)  # Simular operação que leva tempo
    return f"Result: {param1}-{param2}-{call_counter}"

# Função com cache de curta duração para testar expiração
@cache_result(ttl_seconds=1)  # Cache por apenas 1 segundo
async def short_lived_function():
    global call_counter
    call_counter += 1
    return f"Short lived result: {call_counter}"

@pytest.fixture(autouse=True)
def reset_cache_and_counter():
    """Limpa o cache e zera o contador antes de cada teste"""
    global call_counter
    call_counter = 0
    clear_cache()
    yield
    # Também limpa após o teste
    clear_cache()

@pytest.mark.asyncio
async def test_cache_hit():
    """Testa se o cache está armazenando e reutilizando resultados"""
    # Primeira chamada - deve executar a função real
    result1 = await sample_function("test", 123)
    assert call_counter == 1
    
    # Segunda chamada com mesmos parâmetros - deve usar o cache
    result2 = await sample_function("test", 123)
    assert call_counter == 1  # O contador não deve incrementar
    assert result1 == result2
    
    # Chamada com parâmetros diferentes - deve executar a função real novamente
    result3 = await sample_function("test", 456)
    assert call_counter == 2
    assert result1 != result3

@pytest.mark.asyncio
async def test_cache_expiration():
    """Testa se o cache expira corretamente após o TTL"""
    # Primeira chamada
    result1 = await short_lived_function()
    assert call_counter == 1
    
    # Segunda chamada imediata - deve usar cache
    result2 = await short_lived_function()
    assert call_counter == 1
    assert result1 == result2
    
    # Esperar o cache expirar
    await asyncio.sleep(1.1)
    
    # Terceira chamada após expiração - deve executar a função real
    result3 = await short_lived_function()
    assert call_counter == 2
    assert result1 != result3

@pytest.mark.asyncio
async def test_clear_cache():
    """Testa se a função clear_cache limpa corretamente o cache"""
    # Cria algumas entradas de cache
    await sample_function("a", 1)
    await sample_function("b", 2)
    
    # Verifica se existem entradas no cache
    cache_info = get_cache_info()
    assert cache_info["total_entries"] > 0
    
    # Limpa o cache
    clear_cache()
    
    # Verifica se o cache está vazio
    cache_info = get_cache_info()
    assert cache_info["total_entries"] == 0

@pytest.mark.asyncio
async def test_get_cache_info():
    """Testa se a função get_cache_info retorna informações corretas"""
    # Cria uma entrada com TTL curto
    await short_lived_function()
    
    # Verifica informações iniciais
    cache_info = get_cache_info()
    assert cache_info["total_entries"] == 1
    assert cache_info["valid_entries"] == 1
    assert cache_info["expired_entries"] == 0
    
    # Espera o cache expirar
    await asyncio.sleep(1.1)
    
    # Verifica informações após expiração
    cache_info = get_cache_info()
    assert cache_info["total_entries"] == 1
    assert cache_info["valid_entries"] == 0
    assert cache_info["expired_entries"] == 1
