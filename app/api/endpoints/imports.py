from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.scraper.imports_scraper import ImportsScraper

router = APIRouter()

@router.get("/", summary="Dados de importação")
async def get_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retrieve import data for viticulture products.
    
    Retorna dados sobre importação de produtos vitivinícolas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        data = scraper.get_imports_data(year)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados: {str(e)}")
