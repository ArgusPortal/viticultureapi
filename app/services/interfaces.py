"""
Interfaces base para serviços.

Define contratos para os diferentes tipos de serviços na aplicação.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Generic, Protocol

class BaseService(ABC):
    """Interface base para todos os serviços."""
    
    @abstractmethod
    async def process(self, **kwargs) -> Dict[str, Any]:
        """
        Método genérico para processar uma operação no serviço.
        
        Args:
            **kwargs: Parâmetros da operação
            
        Returns:
            Dict com resultado do processamento
        """
        pass

class DataService(BaseService):
    """Interface para serviços que manipulam dados."""
    
    @abstractmethod
    async def get_data(self, **kwargs) -> Dict[str, Any]:
        """
        Obtém dados processados.
        
        Args:
            **kwargs: Parâmetros para filtragem e processamento
            
        Returns:
            Dict com dados processados e metadados
        """
        pass
    
    @abstractmethod
    async def transform_data(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Transforma dados de acordo com regras de negócio.
        
        Args:
            data: Dados a serem transformados
            **kwargs: Parâmetros adicionais
            
        Returns:
            Dict com dados transformados
        """
        pass

class DataTransformer(Protocol):
    """Interface para transformadores de dados."""
    
    def transform(self, data: Any) -> Any:
        """
        Transforma dados de acordo com uma estratégia específica.
        
        Args:
            data: Dados a serem transformados
            
        Returns:
            Dados transformados
        """
        pass

class DataTransformerService(BaseService):
    """Interface para o serviço de transformação de dados."""
    
    @abstractmethod
    async def register_transformer(self, name: str, transformer: DataTransformer) -> None:
        """
        Registra um transformador de dados.
        
        Args:
            name: Nome do transformador
            transformer: Instância do transformador
        """
        pass
    
    @abstractmethod
    async def transform(self, data: Any, transformers: Optional[List[str]] = None) -> Any:
        """
        Transforma dados aplicando um ou mais transformadores em sequência.
        
        Args:
            data: Dados a serem transformados
            transformers: Lista de nomes de transformadores a serem aplicados
            
        Returns:
            Dados transformados
        """
        pass

