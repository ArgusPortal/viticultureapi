"""
Módulo de modelos de dados e schemas.

Este módulo contém:
- Schemas Pydantic para validação de dados
- Modelos de domínio para representar entidades de negócio
- Classes de transformação/conversão de dados
"""

# Re-exportar modelos e fábricas para facilitar importação
from app.models.base import ResponseBase, DataResponse, ErrorResponse
from app.models.production import (
    ProductionRecord, WineProductionRecord, JuiceProductionRecord, 
    DerivativeProductionRecord, ProductionResponse
)
from app.models.trade import (
    TradeRecord, ImportRecord, ExportRecord,
    TradeResponse, ImportResponse, ExportResponse
)
from app.models.commercialization import CommercializationRecord, CommercializationResponse
from app.models.processing import ProcessingRecord, DetailedProcessingRecord, ProcessingResponse

# Exportar fábricas
from app.models.factory import ModelFactory, ResponseFactory

