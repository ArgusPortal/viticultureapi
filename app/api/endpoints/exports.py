from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.scraper.exports_scraper import ExportsScraper

router = APIRouter()

@router.get("/", summary="Dados de exportação")
async def get_export_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retrieve export data for viticulture products.
    
    Retorna dados sobre exportação de produtos vitivinícolas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ExportsScraper()
        data = scraper.get_exports_data(year)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados: {str(e)}")
