from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.scraper.commercialization_scraper import CommercializationScraper
from app.core.security import verify_token
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

@router.get("/", summary="Dados de comercialização")
async def get_commercialization_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)"),
    current_user: str = Depends(verify_token)
):
    """
    Retrieve commercialization data for viticulture products.
    
    Este endpoint requer autenticação. O usuário precisa fornecer um token JWT válido no cabeçalho de autorização.
    
    Retorna dados sobre a comercialização de produtos vitivinícolas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = CommercializationScraper()
        logger.info(f"Fetching commercialization data for year: {year} - requested by user: {current_user}")
        data = scraper.get_commercialization_data(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in commercialization endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de comercialização: {str(e)}"
        )
