"""
Módulo de serviços de negócios.

Este módulo implementa a lógica de negócios da aplicação, conectando
os modelos de dados com os repositórios e implementando regras de negócio.
"""

# Importar serviços principais para facilitar a importação externa
from app.services.data_transformer import DataTransformerServiceImpl

__all__ = ['DataTransformerServiceImpl']

