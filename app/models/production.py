"""
Modelos de domínio para dados de produção.

Define estruturas e validações para dados de produção de vinhos, sucos e derivados.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from app.models.base import ResponseBase, DataResponse, BaseConfig
from app.utils.data_cleaner import safe_float_conversion

class ProductionRecord(BaseModel):
    """Modelo base para um registro de produção de vinho, suco ou derivado."""
    
    produto: str = Field(..., description="Nome do produto")
    quantidade: Union[int, float, str] = Field(
        ..., 
        description="Quantidade produzida (litros)", 
        alias="Quantidade (L.)"
    )
    ano: int = Field(..., description="Ano de referência", alias="Ano")
    
    @validator('quantidade', pre=True)
    def clean_quantidade(cls, v):
        """Converter quantidade para um valor numérico."""
        if isinstance(v, (int, float)):
            return v
        return safe_float_conversion(v)
    
    class Config(BaseConfig):
        """Configuração do modelo ProductionRecord."""
        json_schema_extra = {
            "example": {
                "produto": "Vinho Tinto",
                "Quantidade (L.)": 195031611,
                "Ano": 2022
            }
        }

class WineProductionRecord(ProductionRecord):
    """Modelo para registro de produção de vinho."""
    
    tipo: Optional[str] = Field(None, description="Tipo de vinho (tinto, branco, rosé)")
    
    class Config(ProductionRecord.Config):
        """Configuração do modelo WineProductionRecord."""
        json_schema_extra = {
            "example": {
                "produto": "Vinho Tinto",
                "Quantidade (L.)": 162844214,
                "Ano": 2022,
                "tipo": "Tinto"
            }
        }

class JuiceProductionRecord(ProductionRecord):
    """Modelo para registro de produção de suco de uva."""
    
    class Config(ProductionRecord.Config):
        """Configuração do modelo JuiceProductionRecord."""
        json_schema_extra = {
            "example": {
                "produto": "Suco de Uva Integral",
                "Quantidade (L.)": 65809079,
                "Ano": 2022
            }
        }

class DerivativeProductionRecord(ProductionRecord):
    """Modelo para registro de produção de derivados da uva e vinho."""
    
    class Config(ProductionRecord.Config):
        """Configuração do modelo DerivativeProductionRecord."""
        json_schema_extra = {
            "example": {
                "produto": "Espumante",
                "Quantidade (L.)": 70759,
                "Ano": 2022
            }
        }

# Usar o genérico corretamente para evitar erros de invariância
class ProductionResponse(DataResponse[ProductionRecord]):
    """Resposta contendo dados de produção."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo ProductionResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {"produto": "Vinho Tinto", "Quantidade (L.)": 195031611, "Ano": 2022}
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }

class WineProductionResponse(DataResponse[WineProductionRecord]):
    """Resposta contendo dados de produção de vinhos."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo WineProductionResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {"produto": "Vinho Tinto", "Quantidade (L.)": 162844214, "Ano": 2022, "tipo": "Tinto"}
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }

class JuiceProductionResponse(DataResponse[JuiceProductionRecord]):
    """Resposta contendo dados de produção de sucos."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo JuiceProductionResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {"produto": "Suco de Uva Integral", "Quantidade (L.)": 65809079, "Ano": 2022}
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }

class DerivativeProductionResponse(DataResponse[DerivativeProductionRecord]):
    """Resposta contendo dados de produção de derivados."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo DerivativeProductionResponse."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {"produto": "Espumante", "Quantidade (L.)": 70759, "Ano": 2022}
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }
