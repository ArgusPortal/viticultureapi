from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.scraper.commercialization_scraper import CommercializationScraper
from app.core.security import verify_token
from app.core.cache import cache_result
from app.core.utils import clean_navigation_arrows
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

@router.get("/", response_model=dict, summary="Dados de comercialização de vinhos")
@cache_result(ttl_seconds=3600)
async def get_commercialization_data(
    year: Optional[int] = Query(None, description="Filtrar por ano específico"),
    current_user: str = Depends(verify_token)
):
    """
    Retorna dados de comercialização de vinhos, sucos e derivados no mercado interno brasileiro.
    """
    scraper = CommercializationScraper()
    result = scraper.get_commercialization_data(year)
    
    # Clean the data to remove navigation arrows entries
    if "data" in result and isinstance(result["data"], list):
        result["data"] = clean_navigation_arrows(result["data"])
    
    # Add year to response if filtered
    if year:
        result["ano_filtro"] = year
    
    return result
