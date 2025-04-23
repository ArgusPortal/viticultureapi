"""
Dependências para injeção em endpoints.

Este módulo fornece funções de dependência para o FastAPI injetar
serviços e repositórios nos endpoints.
"""
from fastapi import Depends
from typing import Callable, Dict, Any, Optional

from app.repositories.interfaces import ScrapingRepository, FileRepository
from app.repositories.file_repository import CSVFileRepository
from app.repositories.scraping_repository import BaseScrapingRepository
from app.services.interfaces import DataService, BaseService, DataTransformerService
from app.services.data_transformer import DataTransformerServiceImpl

# Cache de instâncias de repositórios para evitar recriação desnecessária
_repositories = {}
_services = {}

# Dependências para repositórios

async def get_file_repository() -> FileRepository:
    """
    Fornece uma instância do repositório de arquivos CSV.
    
    Returns:
        Uma instância de CSVFileRepository
    """
    if "csv_file_repository" not in _repositories:
        _repositories["csv_file_repository"] = CSVFileRepository()
    return _repositories["csv_file_repository"]

async def get_scraping_repository() -> ScrapingRepository:
    """
    Fornece uma instância do repositório base de scraping.
    
    Returns:
        Uma instância de BaseScrapingRepository
    """
    if "base_scraping_repository" not in _repositories:
        _repositories["base_scraping_repository"] = BaseScrapingRepository()
    return _repositories["base_scraping_repository"]

# Instâncias de serviços
_services = {}

# Dependências para serviços
async def get_data_transformer_service() -> DataTransformerService:
    """
    Fornece uma instância do serviço de transformação de dados.
    
    Returns:
        Uma instância de DataTransformerServiceImpl
    """
    if "data_transformer" not in _services:
        _services["data_transformer"] = DataTransformerServiceImpl()
    return _services["data_transformer"]

async def get_production_service():
    """
    Fornece uma instância do serviço de produção.
    
    Returns:
        Uma instância de ProductionService
    """
    # Será implementado quando criarmos ProductionService
    pass

async def get_imports_service():
    """
    Fornece uma instância do serviço de importação.
    
    Returns:
        Uma instância de ImportsService
    """
    # Será implementado quando criarmos ImportsService
    pass

async def get_exports_service():
    """
    Fornece uma instância do serviço de exportação.
    
    Returns:
        Uma instância de ExportsService
    """
    # Será implementado quando criarmos ExportsService
    pass

async def get_commercialization_service():
    """
    Fornece uma instância do serviço de comercialização.
    
    Returns:
        Uma instância de CommercializationService
    """
    # Será implementado quando criarmos CommercializationService
    pass

async def get_processing_service():
    """
    Fornece uma instância do serviço de processamento.
    
    Returns:
        Uma instância de ProcessingService
    """
    # Será implementado quando criarmos ProcessingService
    pass

