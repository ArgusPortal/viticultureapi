"""
Modelos de domínio para dados de comércio internacional.

Define estruturas e validações para dados de importação e exportação.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from app.models.base import ResponseBase, DataResponse, BaseConfig
from app.utils.data_cleaner import safe_float_conversion

class TradeRecord(BaseModel):
    """Modelo base para um registro de importação ou exportação."""
    
    pais: str = Field(..., description="País de origem/destino", alias="Pais")
    produto: str = Field(..., description="Nome do produto", alias="Produto")
    quantidade: Union[int, float, str] = Field(
        ..., 
        description="Quantidade comercializada", 
        alias="Quantidade"
    )
    valor: Union[int, float, str] = Field(
        ..., 
        description="Valor em US$", 
        alias="Valor"
    )
    ano: int = Field(..., description="Ano de referência", alias="Ano")
    
    @validator('quantidade', 'valor', pre=True)
    def clean_numeric_values(cls, v):
        """Converter valores numéricos."""
        if isinstance(v, (int, float)):
            return v
        return safe_float_conversion(v)
    
    class Config(BaseConfig):
        """Configuração do modelo TradeRecord."""
        allow_population_by_field_name = True
        json_schema_extra = {
            "example": {
                "Pais": "Argentina",
                "Produto": "Vinho Tinto",
                "Quantidade": 5000,
                "Valor": 100000,
                "Ano": 2022
            }
        }

class ImportRecord(TradeRecord):
    """Modelo para registro de importação."""
    
    class Config(TradeRecord.Config):
        """Configuração do modelo ImportRecord."""
        json_schema_extra = {
            "example": {
                "Pais": "Argentina",
                "Produto": "Vinho Tinto",
                "Quantidade": 5000,
                "Valor": 100000,
                "Ano": 2022
            }
        }

class ExportRecord(TradeRecord):
    """Modelo para registro de exportação."""
    
    class Config(TradeRecord.Config):
        """Configuração do modelo ExportRecord."""
        json_schema_extra = {
            "example": {
                "Pais": "EUA",
                "Produto": "Vinho Tinto",
                "Quantidade": 1000,
                "Valor": 50000,
                "Ano": 2022
            }
        }

# Usar o genérico corretamente para evitar erros de invariância
class TradeResponse(DataResponse[TradeRecord]):
    """Resposta base para dados de comércio internacional."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    pais_filtro: Optional[str] = Field(None, description="País filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo TradeResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {
                        "Pais": "Argentina",
                        "Produto": "Vinho Tinto",
                        "Quantidade": 5000,
                        "Valor": 100000,
                        "Ano": 2022
                    }
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }

class ImportResponse(DataResponse[ImportRecord]):
    """Resposta contendo dados de importação."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    pais_filtro: Optional[str] = Field(None, description="País filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo ImportResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {
                        "Pais": "Argentina",
                        "Produto": "Vinho Tinto",
                        "Quantidade": 5000,
                        "Valor": 100000,
                        "Ano": 2022
                    }
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }

class ExportResponse(DataResponse[ExportRecord]):
    """Resposta contendo dados de exportação."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    pais_filtro: Optional[str] = Field(None, description="País filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo ExportResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {
                        "Pais": "EUA",
                        "Produto": "Vinho Tinto",
                        "Quantidade": 1000,
                        "Valor": 50000,
                        "Ano": 2022
                    }
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }
