"""
Interfaces base para estratégias de processamento de dados.

Define contratos para diferentes estratégias de processamento seguindo o padrão Strategy.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')
U = TypeVar('U')

class ProcessingStrategy(ABC):
    """Interface base para estratégias de processamento."""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Processa os dados de acordo com a estratégia implementada.
        
        Args:
            data: Dados a serem processados
            
        Returns:
            Dados processados
        """
        pass

class CleaningStrategy(ProcessingStrategy):
    """Interface para estratégias de limpeza de dados."""
    
    @abstractmethod
    def clean(self, data: Any) -> Any:
        """
        Limpa os dados de acordo com a estratégia específica.
        
        Args:
            data: Dados a serem limpos
            
        Returns:
            Dados limpos
        """
        pass
    
    def process(self, data: Any) -> Any:
        """
        Implementação do método process que chama clean.
        
        Args:
            data: Dados a serem processados
            
        Returns:
            Dados processados
        """
        return self.clean(data)

class EnrichmentStrategy(ProcessingStrategy):
    """Interface para estratégias de enriquecimento de dados."""
    
    @abstractmethod
    def enrich(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Enriquece os dados com informações adicionais.
        
        Args:
            data: Dados a serem enriquecidos
            context: Contexto opcional para enriquecimento
            
        Returns:
            Dados enriquecidos
        """
        pass
    
    def process(self, data: Any) -> Any:
        """
        Implementação do método process que chama enrich.
        
        Args:
            data: Dados a serem processados
            
        Returns:
            Dados processados
        """
        return self.enrich(data)

class ValidationStrategy(ProcessingStrategy):
    """Interface para estratégias de validação de dados."""
    
    @abstractmethod
    def validate(self, data: Any) -> Dict[str, Any]:
        """
        Valida os dados de acordo com regras específicas.
        
        Args:
            data: Dados a serem validados
            
        Returns:
            Dict com resultado da validação (validado, erros)
        """
        pass
    
    def process(self, data: Any) -> Dict[str, Any]:
        """
        Implementação do método process que chama validate.
        
        Args:
            data: Dados a serem processados
            
        Returns:
            Resultado da validação
        """
        return self.validate(data)

class CompositeStrategy(ProcessingStrategy):
    """Estratégia composta que aplica múltiplas estratégias em sequência."""
    
    def __init__(self, strategies: Optional[List[ProcessingStrategy]] = None):
        """
        Inicializa a estratégia composta.
        
        Args:
            strategies: Lista de estratégias a serem aplicadas em sequência
        """
        self.strategies = strategies or []
    
    def add_strategy(self, strategy: ProcessingStrategy) -> None:
        """
        Adiciona uma estratégia à lista.
        
        Args:
            strategy: Estratégia a ser adicionada
        """
        self.strategies.append(strategy)
    
    def process(self, data: Any) -> Any:
        """
        Processa os dados aplicando cada estratégia em sequência.
        
        Args:
            data: Dados a serem processados
            
        Returns:
            Dados processados
        """
        result = data
        for strategy in self.strategies:
            result = strategy.process(result)
        return result
