from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.scraper.imports_scraper import ImportsScraper
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

def build_api_response(data, year=None):
    """Build standardized API response from scraped data"""
    if not data or not isinstance(data, dict):
        logger.warning("Invalid data format received")
        raise HTTPException(
            status_code=404,
            detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
        )
        
    if "error" in data:
        logger.error(f"Error in scraped data: {data['error']}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar dados: {data['error']}"
        )
        
    if not data.get("data") or len(data.get("data", [])) == 0:
        logger.warning(f"No data returned for year {year}")
        raise HTTPException(
            status_code=404,
            detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
        )
    
    return {
        "data": data.get("data", []),
        "total": len(data.get("data", [])),
        "ano_filtro": year,
        "source_url": data.get("source_url", ""),
        "source": data.get("source", "unknown")
    }

@router.get("/", summary="Dados de importação")
async def get_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados gerais sobre importação de produtos vitivinícolas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        logger.info(f"Fetching import data for year: {year}")
        data = scraper.get_imports_data(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in imports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de importação: {str(e)}"
        )

@router.get("/wine", summary="Dados de importação de vinhos")
async def get_wine_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre importação de vinhos, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        logger.info(f"Fetching wine import data for year: {year}")
        data = scraper.get_wine_imports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in wine imports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de importação de vinhos: {str(e)}"
        )

@router.get("/fresh", summary="Dados de importação de uvas frescas")
async def get_fresh_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre importação de uvas frescas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        logger.info(f"Fetching fresh grape import data for year: {year}")
        data = scraper.get_fresh_imports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in fresh grape imports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de importação de uvas frescas: {str(e)}"
        )

@router.get("/juice", summary="Dados de importação de sucos")
async def get_juice_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre importação de sucos, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        logger.info(f"Fetching juice import data for year: {year}")
        data = scraper.get_juice_imports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in juice imports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de importação de sucos: {str(e)}"
        )

@router.get("/sparkling", summary="Dados de importação de espumantes")
async def get_sparkling_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre importação de espumantes, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        logger.info(f"Fetching sparkling import data for year: {year}")
        data = scraper.get_sparkling_imports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in sparkling imports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de importação de espumantes: {str(e)}"
        )

@router.get("/raisins", summary="Dados de importação de passas")
async def get_raisins_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre importação de passas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        logger.info(f"Fetching raisins import data for year: {year}")
        data = scraper.get_raisins_imports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in raisins imports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de importação de passas: {str(e)}"
        )
