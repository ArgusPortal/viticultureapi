"""
Interfaces base para repositórios.

Define contratos para os diferentes tipos de repositórios na aplicação.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Generic

# Definir tipo genérico T para ser usado nas interfaces
T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Interface base para todos os repositórios."""
    
    @abstractmethod
    async def get_data(self, **kwargs) -> Dict[str, Any]:
        """
        Obtém dados do repositório.
        
        Args:
            **kwargs: Parâmetros de filtragem
            
        Returns:
            Dict com dados e metadados
        """
        pass

class ScrapingRepository(BaseRepository[T]):
    """Interface para repositórios baseados em web scraping."""
    
    @abstractmethod
    async def scrape_data(self, category: str, year: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """
        Extrai dados via web scraping.
        
        Args:
            category: Categoria de dados (production, imports, exports, etc.)
            year: Ano para filtrar os dados, se aplicável
            **kwargs: Parâmetros adicionais para controlar o scraping
            
        Returns:
            Dict com dados extraídos e metadados
        """
        pass
    
    @abstractmethod
    async def fallback_to_local(self, category: str, subcategory: Optional[str] = None, 
                               year: Optional[int] = None) -> Dict[str, Any]:
        """
        Método de fallback para quando o scraping falhar.
        
        Args:
            category: Categoria de dados (production, imports, exports, etc.)
            subcategory: Subcategoria de dados, se aplicável
            year: Ano para filtrar os dados, se aplicável
            
        Returns:
            Dict com dados de fallback e metadados
        """
        pass

class FileRepository(BaseRepository[T]):
    """Interface para repositórios baseados em arquivos locais."""
    
    @abstractmethod
    async def read_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Lê dados de um arquivo local.
        
        Args:
            file_path: Caminho para o arquivo
            **kwargs: Parâmetros adicionais
            
        Returns:
            Dict com dados do arquivo e metadados
        """
        pass
    
    @abstractmethod
    async def write_file(self, file_path: str, data: Any, **kwargs) -> bool:
        """
        Escreve dados em um arquivo local.
        
        Args:
            file_path: Caminho para o arquivo
            data: Dados a serem escritos
            **kwargs: Parâmetros adicionais
            
        Returns:
            True se a operação foi bem-sucedida, False caso contrário
        """
        pass
