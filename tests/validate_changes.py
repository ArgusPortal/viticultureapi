"""
Script para validar as alterações realizadas no sistema ViticultureAPI.
Foca em testar o cache e o sistema de validação de dados.
"""
import asyncio
import time
import pandas as pd
import logging
from datetime import datetime
from pprint import pprint

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validation_script")

# Importações do sistema
from app.core.cache import cache_result, get_cache_info, clear_cache
from app.core.validation.validators import (
    StringValidator, NumericValidator, DateValidator, DictValidator, ListValidator
)

async def test_cache_decorator():
    """Testa o funcionamento do decorator cache_result."""
    logger.info("=== Testando decorator cache_result ===")
    
    # Definir uma função de teste com cache
    @cache_result(ttl_seconds_or_func=5)
    async def slow_function(param1, param2=None):
        """Função que simula uma operação lenta"""
        await asyncio.sleep(0.5)  # Simulação de operação demorada
        return f"Resultado: {param1}-{param2}-{time.time()}"
    
    # Primeira chamada (sem cache)
    start_time = time.time()
    result1 = await slow_function("teste", 123)
    time1 = time.time() - start_time
    logger.info(f"Primeira chamada: {time1:.2f}s - {result1}")
    
    # Segunda chamada (deve usar cache)
    start_time = time.time()
    result2 = await slow_function("teste", 123)
    time2 = time.time() - start_time
    logger.info(f"Segunda chamada: {time2:.2f}s - {result2}")
    
    # Verificação
    if time2 < time1 and result1 == result2:
        logger.info("✅ Cache funcionando corretamente")
    else:
        logger.error("❌ Cache não está funcionando como esperado")
    
    # Mostrar informações do cache
    cache_info = get_cache_info()
    logger.info(f"Info do cache: {len(cache_info['entries'])} entradas")
    
    # Limpar o cache para não afetar outros testes
    await clear_cache()
    logger.info("Cache limpo")

def test_validators():
    """Testa o funcionamento dos validadores."""
    logger.info("\n=== Testando validadores ===")
    
    # StringValidator
    validator = StringValidator(
        field_name="nome",
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-Z\s]+$'
    )
    
    # Teste com valor válido
    result1 = validator.validate("Nome válido")
    logger.info(f"StringValidator - Valor válido: {result1.is_valid}")
    
    # Teste com valor inválido
    result2 = validator.validate("123")
    logger.info(f"StringValidator - Valor inválido: {result2.is_valid}")
    if not result2.is_valid:
        logger.info(f"  - Problemas: {len(result2.issues)}")
        for issue in result2.issues:
            logger.info(f"  - {issue}")
    
    # NumericValidator
    num_validator = NumericValidator(
        field_name="idade",
        min_value=18,
        max_value=100
    )
    
    result3 = num_validator.validate(25)
    logger.info(f"NumericValidator - Valor válido: {result3.is_valid}")
    
    result4 = num_validator.validate(15)
    logger.info(f"NumericValidator - Valor inválido: {result4.is_valid}")
    
    # Validar um DataFrame
    df = pd.DataFrame({
        'nome': ['Ana', 'Pedro', 'Jo'],
        'idade': [25, 40, 15],
        'ativo': [True, True, False]
    })
    
    logger.info("\nValidando DataFrame:")
    logger.info(df)
    
    from app.core.validation.validators import DataFrameValidator
    
    df_validator = DataFrameValidator(
        field_name="usuarios",
        column_validators={
            'nome': StringValidator('nome', min_length=3),
            'idade': NumericValidator('idade', min_value=18)
        }
    )
    
    result5 = df_validator.validate(df)
    logger.info(f"DataFrame válido: {result5.is_valid}")
    logger.info(f"Problemas: {len(result5.issues)}")
    for issue in result5.issues:
        logger.info(f"- {issue}")

async def test_pipeline_factory():
    """Testa o funcionamento do ConcreteCacheLoader no pipeline factory."""
    logger.info("\n=== Testando ConcreteCacheLoader ===")
    
    from app.core.pipeline_factory import ConcreteCacheLoader
    
    # Criar um loader
    cache_loader = ConcreteCacheLoader(
        key="teste_pipeline",
        ttl_seconds=30,
        tags=["teste", "validacao"]
    )
    
    # Testar carregamento de dados
    data = {"test": True, "value": 123, "timestamp": str(datetime.now())}
    result = cache_loader.load(data)
    
    logger.info(f"Dados salvos no cache: {result}")
    
    # Verificar se estão no cache
    from app.core.cache import CACHE
    
    if "teste_pipeline" in CACHE:
        cached_data, expiry = CACHE["teste_pipeline"]
        logger.info(f"✅ Dados encontrados no cache")
        logger.info(f"Dados: {cached_data}")
        logger.info(f"Expiração: {expiry}")
    else:
        logger.error("❌ Dados não foram salvos no cache")

async def main():
    """Função principal para executar todos os testes de validação."""
    logger.info("Iniciando validação das alterações...")
    
    await test_cache_decorator()
    test_validators()
    await test_pipeline_factory()
    
    logger.info("\nValidação concluída!")

if __name__ == "__main__":
    asyncio.run(main())
