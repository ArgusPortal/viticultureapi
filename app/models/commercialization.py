"""
Modelos de domínio para dados de comercialização.

Define estruturas e validações para dados de comercialização no mercado interno.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from app.models.base import ResponseBase, DataResponse, BaseConfig
from app.utils.data_cleaner import safe_float_conversion

class CommercializationRecord(BaseModel):
    """Modelo para um registro de comercialização no mercado interno."""
    
    produto: str = Field(..., description="Nome do produto", alias="Produto")
    quantidade: Union[int, float, str] = Field(
        ..., 
        description="Quantidade comercializada (litros)", 
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
        """Configuração do modelo CommercializationRecord."""
        json_schema_extra = {
            "example": {
                "Produto": "Vinho Tinto",
                "Quantidade (L.)": 195031611,
                "Ano": 2022
            }
        }

# Usar o genérico corretamente para evitar erros de invariância
class CommercializationResponse(DataResponse[CommercializationRecord]):
    """Resposta contendo dados de comercialização."""
    
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    
    class Config(DataResponse.Config):
        """Configuração do modelo CommercializationResponse que herda de DataResponse.Config."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [
                    {"Produto": "Vinho Tinto", "Quantidade (L.)": 195031611, "Ano": 2022}
                ],
                "count": 1,
                "ano_filtro": 2022
            }
        }
