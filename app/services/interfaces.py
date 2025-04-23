"""
Interfaces base para serviços.

Define contratos para os diferentes tipos de serviços na aplicação.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

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

