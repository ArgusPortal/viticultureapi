from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class WineProduction(BaseModel):
    produto: str = Field(..., description="Nome do produto")
    quantidade: float = Field(..., description="Quantidade em litros")
    ano: Optional[int] = Field(None, description="Ano de referência")
    
    class Config:
        schema_extra = {
            "example": {
                "produto": "Vinho tinto de mesa",
                "quantidade": 123456.78,
                "ano": 2022
            }
        }

class WineProductionList(BaseModel):
    data: List[WineProduction]
    total: int
    ano: Optional[int] = None
