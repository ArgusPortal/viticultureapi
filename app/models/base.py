"""
Modelos base para a aplicação.

Define estruturas de dados básicas e métodos de validação.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, TypeVar, Generic
from datetime import datetime

# Definir um tipo genérico T para os registros
T = TypeVar('T', bound=BaseModel)

# Definir uma classe Config base que pode ser herdada
class BaseConfig:
    """Configuração base compartilhada por todos os modelos."""
    arbitrary_types_allowed = True

class ResponseBase(BaseModel):
    """Modelo base para respostas da API."""
    
    source: str = Field(..., description="Fonte dos dados (scraping, csv, cache, etc)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da resposta")
    
    class Config(BaseConfig):
        """Configuração do modelo ResponseBase."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00"
            }
        }

class DataResponse(ResponseBase, Generic[T]):
    """Modelo para respostas contendo dados."""
    
    data: List[T] = Field(..., description="Lista de registros")
    count: int = Field(..., description="Número de registros")
    
    class Config(ResponseBase.Config):
        """Configuração do modelo DataResponse que herda de ResponseBase.Config."""
        json_schema_extra = {
            "example": {
                "source": "web_scraping",
                "timestamp": "2023-01-01T00:00:00",
                "data": [{"Produto": "Vinho Tinto", "Quantidade (L.)": "1000000", "Ano": 2022}],
                "count": 1
            }
        }

class ErrorResponse(BaseModel):
    """Modelo para respostas de erro."""
    
    detail: str = Field(..., description="Descrição do erro")
    code: Optional[str] = Field(None, description="Código de erro")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do erro")
    
    class Config(BaseConfig):
        """Configuração do modelo ErrorResponse."""
        json_schema_extra = {
            "example": {
                "detail": "Erro ao obter dados",
                "code": "DATA_ERROR",
                "timestamp": "2023-01-01T00:00:00"
            }
        }

