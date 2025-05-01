import sys
import os
import pytest
import asyncio
import logging
from datetime import datetime, timedelta
import time

# Adicionar o caminho raiz do projeto ao Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging to debug cache issues
logging.basicConfig(level=logging.DEBUG)
cache_logger = logging.getLogger('app.core.cache')
cache_logger.setLevel(logging.DEBUG)

# Importar corretamente do pacote app.core.cache
# ao invés de tentar importar do módulo cache.py diretamente
from app.core.cache import cache_result, clear_cache, clear_cache_sync, get_cache_info, CACHE
# Para testes que precisam acessar o dicionário CACHE diretamente
from app.core.cache.memory_provider import MemoryCacheProvider
from app.core.cache.factory import CacheFactory

# Inicializar o CacheFactory para os testes
factory = CacheFactory.get_instance()
default_provider = factory.get_provider(None)
print(f"Using cache provider: {default_provider.__class__.__name__}")

# Contador para verificar quantas vezes a função real foi chamada
call_counter = 0

# Função de teste que será decorada com cache
# Use apenas o decorador sem nenhum parâmetro para evitar problemas com o nome do parâmetro
@cache_result  # Teste com forma simplificada sem argumentos
async def sample_function(param1, param2=None):
    """Função de exemplo que simula uma operação demorada e incrementa o contador"""
    global call_counter
    call_counter += 1
    await asyncio.sleep(0.1)  # Simular operação que leva tempo
    result = f"Result: {param1}-{param2}-{call_counter}"
    print(f"Generated result: {result}")
    return result

# Função com cache de curta duração para testar expiração
@cache_result(ttl_seconds_or_func=1)  # Cache por apenas 1 segundo
async def short_lived_function():
    global call_counter
    call_counter += 1
    return f"Short lived result: {call_counter}"

@pytest.fixture(autouse=True)
async def reset_cache_and_counter():
    """Limpa o cache e zera o contador antes de cada teste"""
    global call_counter
    call_counter = 0
    
    await clear_cache()  # Usar função importada para limpar o cache
    yield
    # Também limpa após o teste
    await clear_cache()

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
    
    # Debug: mostra o conteúdo do cache
    print(f"CACHE content: {CACHE}")
    print(f"Cache info: {get_cache_info()}")
    
    # Verificar que o cache está funcionando
    # Não precisamos acessar o provider diretamente, o comportamento
    # da função já comprova que o cache está funcionando corretamente
    # porque o contador não incrementou na segunda chamada
    assert call_counter == 2, "Cache não está funcionando corretamente"
    
    # Se chegarmos até aqui, o cache está funcionando mesmo que o CACHE global esteja vazio
    # porque o contador não incrementou na segunda chamada com os mesmos parâmetros

@pytest.mark.asyncio
async def test_cache_expiration():
    """Testa se o cache expira corretamente após o TTL"""
    # Primeira chamada
    result1 = await short_lived_function()
    assert call_counter == 1
    print(f"First call result: {result1}")
    
    # Segunda chamada imediata - deve usar cache
    result2 = await short_lived_function()
    assert call_counter == 1
    assert result1 == result2
    print(f"Second call (cached) result: {result2}")
    
    print("Waiting for cache to expire (TTL=1s)...")
    # Increase sleep time to ensure cache expiry (timing can be imprecise)
    await asyncio.sleep(2.0)  # Increased from 1.1s to 2.0s to ensure expiration
    print("Sleep completed, cache should be expired now")
    
    # Optional: Force garbage collection to help with timely cache cleanup
    import gc
    gc.collect()
    
    # Print cache status before final call
    cache_info = get_cache_info()
    print(f"Cache info before final call: {cache_info}")
    print(f"Current counter: {call_counter}")
    
    # Terceira chamada após expiração - deve executar a função real
    result3 = await short_lived_function()
    print(f"Third call result: {result3}, counter: {call_counter}")
    
    # Check that the counter increased (cache missed)
    assert call_counter == 2, f"Cache still active! Counter: {call_counter}, results: {result1} vs {result3}"
    assert result1 != result3, "Results should be different after cache expiry"

@pytest.mark.asyncio
async def test_clear_cache():
    """Testa se a função clear_cache limpa corretamente o cache"""
    # Cria algumas entradas de cache
    result1 = await sample_function("test_clear", 1)
    assert call_counter == 1
    
    # Verify the cache is working by calling again with the same parameters
    result2 = await sample_function("test_clear", 1)
    assert call_counter == 1  # Counter shouldn't increase when cache is used
    assert result1 == result2  # Results should match
    
    # Optional: Check cache info for debugging
    cache_info = get_cache_info()
    print(f"Cache info before clearing: {cache_info}")
    
    # Limpa o cache
    await clear_cache()
    print("Cache cleared")
    
    # Optional: Check cache info after clearing
    cache_info = get_cache_info()
    print(f"Cache info after clearing: {cache_info}")
    
    # After clearing, the same function call should execute the real function again
    result3 = await sample_function("test_clear", 1)
    assert call_counter == 2  # Counter should increase after cache is cleared
    assert result1 != result3  # Result should be different as it's regenerated
    
    # Verify caching works again after clearing
    result4 = await sample_function("test_clear", 1)
    assert call_counter == 2  # Counter shouldn't increase again
    assert result3 == result4  # Results should match again

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

# Adicionar este código ao final do arquivo para permitir execução direta
if __name__ == "__main__":
    import pytest
    
    print("Executando testes de cache...")
    
    # Executar os testes com sinalizadores para mostrar mais detalhes
    pytest_args = [
        "-v",                      # Modo verboso
        "--no-header",             # Remove o cabeçalho
        "--no-summary",            # Remove o resumo
        "-xvs",                    # Mostrar saída extra e parar no primeiro erro
        __file__,                  # Testar este arquivo
    ]
    
    result = pytest.main(pytest_args)
    
    # Mostrar resultado final
    if result == 0:
        print("\n✅ Todos os testes de cache passaram com sucesso!")
    else:
        print(f"\n❌ Alguns testes falharam. Código de saída: {result}")
