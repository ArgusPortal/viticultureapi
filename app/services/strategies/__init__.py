"""
Pacote de estratégias de processamento de dados.

Implementa o padrão Strategy para diferentes aspectos do processamento de dados.
"""
from app.services.strategies.base import (
    ProcessingStrategy, 
    CleaningStrategy, 
    EnrichmentStrategy, 
    ValidationStrategy,
    CompositeStrategy
)

from app.services.strategies.cleaning_strategies import (
    NavigationArrowsCleaningStrategy,
    EmptyValueCleaningStrategy,
    OutlierDetectionStrategy
)

__all__ = [
    # Base strategies
    'ProcessingStrategy',
    'CleaningStrategy',
    'EnrichmentStrategy',
    'ValidationStrategy',
    'CompositeStrategy',
    
    # Cleaning strategies
    'NavigationArrowsCleaningStrategy',
    'EmptyValueCleaningStrategy',
    'OutlierDetectionStrategy',
]
