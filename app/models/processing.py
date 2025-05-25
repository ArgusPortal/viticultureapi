"""
Modelos de domínio para dados de processamento de uvas.

Define estruturas e validações para dados de processamento industrial.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal

from app.models.base import ResponseBase, DataResponse, BaseConfig
from app.utils.data_cleaner import safe_float_conversion

class ProcessingRecord(BaseModel):
    """Modelo para um registro de processamento de uvas."""
    
    grupo: str = Field(..., description="Grupo de uva (vinífera, americana, etc.)", alias="Grupo")
    quantidade: Union[int, float, str] = Field(
        ..., 
        description="Quantidade processada (kg)", 
        alias="Quantidade (kg)"
    )
    ano: int = Field(..., description="Ano de referência", alias="Ano")
    
    @validator('quantidade', pre=True)
    def clean_quantidade(cls, v):
        """Converter quantidade para um valor numérico."""
        if isinstance(v, (int, float)):
            return v
        return safe_float_conversion(v)
    
    class Config(BaseConfig):
        """Configuração do modelo ProcessingRecord."""
        json_schema_extra = {
            "example": {
                "Grupo": "Uvas Viníferas",
                "Quantidade (kg)": 450000000,
                "Ano": 2022
            }
        }

class DetailedProcessingRecord(ProcessingRecord):
    """Modelo para um registro detalhado de processamento de uvas."""
    
    variedade: str = Field(..., description="Variedade da uva", alias="Variedade")
    
    class Config(ProcessingRecord.Config):
        """Configuração do modelo DetailedProcessingRecord."""
        json_schema_extra = {
            "example": {
                "Grupo": "Uvas Viníferas",
                "Variedade": "Cabernet Sauvignon",
                "Quantidade (kg)": 120000000,
                "Ano": 2022
            }
        }

# Usar o genérico corretamente para evitar erros de invariância
class ProcessingResponse(DataResponse[ProcessingRecord]):
    """Resposta contendo dados de processamento."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo ProcessingResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {"Grupo": "Uvas Viníferas", "Quantidade (kg)": 450000000, "Ano": 2022}
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }

class DetailedProcessingResponse(DataResponse[DetailedProcessingRecord]):
    """Resposta contendo dados detalhados de processamento."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo DetailedProcessingResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {
                        "Grupo": "Uvas Viníferas", 
                        "Variedade": "Cabernet Sauvignon",
                        "Quantidade (kg)": 120000000, 
                        "Ano": 2022
                    }
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }
