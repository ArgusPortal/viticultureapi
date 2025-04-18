from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.scraper.processing_scraper import ProcessingScraper

router = APIRouter()

@router.get("/", summary="Dados de processamento")
async def get_processing_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retrieve processing data for viticulture.
    
    Retorna dados sobre o processamento vitivinícola, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProcessingScraper()
        data = scraper.get_processing_data(year)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados: {str(e)}")
