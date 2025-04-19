from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.scraper.processing_scraper import ProcessingScraper
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

@router.get("/", summary="Dados gerais de processamento")
async def get_processing_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retrieve general processing data for viticulture.
    
    Retorna dados gerais sobre o processamento vitivinícola, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching processing data for year: {year}")
        data = scraper.get_processing_data(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in processing endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de processamento: {str(e)}"
        )

@router.get("/vinifera", summary="Dados de processamento de uvas viníferas")
async def get_vinifera_processing_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre o processamento de uvas viníferas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching vinifera grape processing data for year: {year}")
        data = scraper.get_vinifera_processing(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in vinifera processing endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de processamento de uvas viníferas: {str(e)}"
        )

@router.get("/american", summary="Dados de processamento de uvas americanas e híbridas")
async def get_american_processing_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre o processamento de uvas americanas e híbridas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching American grape processing data for year: {year}")
        data = scraper.get_american_processing(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in American processing endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de processamento de uvas americanas e híbridas: {str(e)}"
        )

@router.get("/table", summary="Dados de processamento de uvas de mesa")
async def get_table_processing_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre o processamento de uvas de mesa, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching table grape processing data for year: {year}")
        data = scraper.get_table_processing(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in table processing endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de processamento de uvas de mesa: {str(e)}"
        )

@router.get("/unclassified", summary="Dados de processamento de uvas sem classificação")
async def get_unclassified_processing_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre o processamento de uvas sem classificação, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching unclassified grape processing data for year: {year}")
        data = scraper.get_unclassified_processing(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in unclassified processing endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de processamento de uvas sem classificação: {str(e)}"
        )
