"""
Serviço de transformação de dados.

Implementa o padrão Strategy para transformação de dados,
permitindo registrar e aplicar diferentes estratégias de transformação.
"""
import logging
from typing import Dict, List, Any, Optional, Type, Union
import inspect

from app.services.interfaces import DataTransformerService, DataTransformer
from app.services.transformers import BaseTransformer, NavigationArrowsCleaner, NumericValueCleaner

logger = logging.getLogger(__name__)

class DataTransformerServiceImpl(DataTransformerService):
    """
    Implementação do serviço de transformação de dados.
    
    Este serviço permite registrar e aplicar transformadores de dados
    seguindo o padrão Strategy.
    """
    
    def __init__(self):
        """Inicializa o serviço com transformadores padrão."""
        self._transformers: Dict[str, DataTransformer] = {}
        
        # Registrar transformadores padrão
        self._register_default_transformers()
    
    def _register_default_transformers(self) -> None:
        """Registra os transformadores padrão."""
        self._transformers["navigation_arrows"] = NavigationArrowsCleaner()
        self._transformers["numeric_values"] = NumericValueCleaner()
    
    async def process(self, **kwargs) -> Dict[str, Any]:
        """
        Processa uma operação no serviço.
        
        Args:
            **kwargs: Parâmetros da operação
            
        Returns:
            Dict com resultado do processamento
        """
        data = kwargs.get("data")
        transformers = kwargs.get("transformers", [])
        
        if not data:
            return {"error": "No data provided", "success": False}
        
        try:
            result = await self.transform(data, transformers)
            return {"data": result, "success": True}
        except Exception as e:
            logger.error(f"Error transforming data: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def register_transformer(self, name: str, transformer: DataTransformer) -> None:
        """
        Registra um transformador de dados.
        
        Args:
            name: Nome do transformador
            transformer: Instância do transformador
        """
        if name in self._transformers:
            logger.warning(f"Transformer '{name}' already registered. Overwriting.")
        
        self._transformers[name] = transformer
        logger.info(f"Registered transformer: {name}")
    
    async def transform(self, data: Any, transformers: Optional[List[str]] = None) -> Any:
        """
        Transforma dados aplicando um ou mais transformadores em sequência.
        
        Args:
            data: Dados a serem transformados
            transformers: Lista de nomes de transformadores a serem aplicados.
                          Se None, aplica apenas o transformador "navigation_arrows".
            
        Returns:
            Dados transformados
        """
        if transformers is None:
            transformers = ["navigation_arrows"]
        
        result = data
        for transformer_name in transformers:
            transformer = self._transformers.get(transformer_name)
            if transformer is None:
                logger.warning(f"Transformer '{transformer_name}' not found. Skipping.")
                continue
            
            result = transformer.transform(result)
            logger.debug(f"Applied transformer '{transformer_name}'")
        
        return result
    
    def get_available_transformers(self) -> List[str]:
        """
        Retorna a lista de transformadores disponíveis.
        
        Returns:
            Lista de nomes de transformadores
        """
        return list(self._transformers.keys())
