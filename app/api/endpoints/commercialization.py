from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any, List
from app.scraper.commercialization_scraper import CommercializationScraper
from app.core.security import verify_token
from app.core.cache import cache_result
from app.utils.data_cleaner import clean_navigation_arrows
from app.models.commercialization import CommercializationResponse, CommercializationRecord
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=Dict[str, Any], summary="Dados de comercialização de vinhos")
@cache_result(ttl_seconds_or_func=3600)  # Atualizado para usar o parâmetro correto
async def get_commercialization_data(
    year: Optional[int] = Query(None, description="Filtrar por ano específico"),
    current_user: str = Depends(verify_token)
):
    """
    Retorna dados de comercialização de vinhos, sucos e derivados no mercado interno brasileiro.
    """
    try:
        scraper = CommercializationScraper()
        result = scraper.get_commercialization_data(year)
        
        # Clean the data to remove navigation arrows entries
        if "data" in result and isinstance(result["data"], list):
            result["data"] = clean_navigation_arrows(result["data"])
        
        # Add year to response if filtered
        if year:
            result["ano_filtro"] = year
        
        # Ensure there is a count field
        if "data" in result and isinstance(result["data"], list) and "count" not in result:
            result["count"] = len(result["data"])
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter dados de comercialização: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar dados de comercialização: {str(e)}"
        )
