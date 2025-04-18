from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.scraper.commercialization_scraper import CommercializationScraper

router = APIRouter()

@router.get("/", summary="Dados de comercialização")
async def get_commercialization_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retrieve commercialization data for viticulture products.
    
    Retorna dados sobre a comercialização de produtos vitivinícolas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = CommercializationScraper()
        data = scraper.get_commercialization_data(year)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados: {str(e)}")
