from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.scraper.exports_scraper import ExportsScraper
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

@router.get("/", 
    summary="Dados de Exportação", 
    response_description="Dados combinados de exportação de todas as categorias")
async def get_exports_data(
    year: Optional[int] = Query(None, 
                             description="Ano de referência dos dados (ex: 2022)", 
                             example=2022,
                             ge=1970, 
                             le=2023)
):
    """
    Retorna dados agregados de exportação de todas as categorias de produtos.
    
    ## Descrição
    
    Este endpoint combina dados de exportação de todos os tipos de produtos vitivinícolas 
    disponíveis no site VitiBrasil, incluindo vinhos de mesa, espumantes, uvas frescas e 
    suco de uva. É útil para obter uma visão geral completa das exportações do setor
    vitivinícola brasileiro.
    
    ## Categorias incluídas
    
    - **Vinhos de mesa**: Vinhos tintos, brancos e rosados
    - **Espumantes**: Vinhos espumantes e frisantes
    - **Uvas frescas**: Uvas in natura para consumo
    - **Suco de uva**: Incluindo integral, concentrado e reconstituído
    
    ## Parâmetros
    
    - **year**: Opcional. Filtra os dados para mostrar apenas o ano especificado.
                Se não for fornecido, retorna dados de todos os anos disponíveis.
    
    ## Dados retornados
    
    Cada registro contém informações sobre o país de destino, quantidade exportada, 
    valor em dólares e um identificador de categoria que permite saber a qual tipo de 
    produto o registro se refere.
    """
    try:
        scraper = ExportsScraper()
        logger.info(f"Fetching export data for year: {year}")
        data = scraper.get_exports_data(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in exports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de exportação: {str(e)}"
        )

@router.get("/vinhos", summary="Dados de Exportação de Vinhos de Mesa")
async def get_wine_export_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre exportação de vinhos de mesa, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ExportsScraper()
        logger.info(f"Fetching wine export data for year: {year}")
        data = scraper.get_wine_exports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in wine exports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de exportação de vinhos: {str(e)}"
        )

@router.get("/espumantes", summary="Dados de Exportação de Espumantes")
async def get_sparkling_export_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre exportação de espumantes, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ExportsScraper()
        logger.info(f"Fetching sparkling wine export data for year: {year}")
        data = scraper.get_sparkling_exports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in sparkling exports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de exportação de espumantes: {str(e)}"
        )

@router.get("/uvas-frescas", summary="Dados de Exportação de Uvas Frescas")
async def get_fresh_grape_export_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre exportação de uvas frescas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ExportsScraper()
        logger.info(f"Fetching fresh grape export data for year: {year}")
        data = scraper.get_fresh_exports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in fresh grape exports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de exportação de uvas frescas: {str(e)}"
        )

@router.get("/suco", summary="Dados de Exportação de Suco de Uva")
async def get_juice_export_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre exportação de suco de uva, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ExportsScraper()
        logger.info(f"Fetching grape juice export data for year: {year}")
        data = scraper.get_juice_exports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in grape juice exports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de exportação de suco de uva: {str(e)}"
        )
