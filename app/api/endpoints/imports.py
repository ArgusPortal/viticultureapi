from fastapi import APIRouter, HTTPException, Query, Response, status
from typing import Optional, Dict, Any, List
from app.scraper.imports_scraper import ImportsScraper
import logging
import traceback
import json

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
        # Instead of 404, return empty data with status 200
        return {
            "data": [],
            "total": 0,
            "ano_filtro": year,
            "source_url": data.get("source_url", ""),
            "source": "no_data",
            "message": f"Não foram encontrados dados para o ano {year if year else 'atual'}"
        }
    
    return {
        "data": data.get("data", []),
        "total": len(data.get("data", [])),
        "ano_filtro": year,
        "source_url": data.get("source_url", ""),
        "source": data.get("source", "unknown")
    }

@router.get("/", 
    summary="Dados de Importação",
    response_description="Dados combinados de importação de todas as categorias")
async def get_imports_data(
    year: Optional[int] = Query(None, 
                             description="Ano de referência dos dados", 
                             example=2022,
                             ge=1970, 
                             le=2023)
):
    """
    Retorna dados agregados de importação de todas as categorias de produtos.
    
    ## Descrição
    
    Este endpoint combina dados de importação de todos os tipos de produtos vitivinícolas 
    disponíveis no site VitiBrasil, incluindo vinhos, espumantes, uvas frescas, uvas passas
    e suco de uva. É útil para obter uma visão geral completa das importações do setor
    vitivinícola brasileiro.
    
    ## Categorias incluídas
    
    - **Vinhos**: Vinhos tintos, brancos e rosados de diversos países
    - **Espumantes**: Vinhos espumantes e champanhes
    - **Uvas frescas**: Uvas in natura para consumo
    - **Uvas passas**: Uvas desidratadas para consumo
    - **Suco de uva**: Incluindo integral, concentrado e reconstituído
    
    ## Parâmetros
    
    - **year**: Opcional. Filtra os dados para mostrar apenas o ano especificado.
                Se não for fornecido, retorna dados de todos os anos disponíveis.
    
    ## Dados retornados
    
    Cada registro contém informações sobre o país de origem, quantidade importada, 
    valor em dólares e um identificador de categoria que permite saber a qual tipo de 
    produto o registro se refere.
    
    ## Metodologia
    
    Os dados são obtidos combinando as informações de diversos sub-endpoints, garantindo
    que mesmo quando o endpoint principal de importações apresenta problemas, os dados
    possam ser recuperados de fontes alternativas.
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

@router.get("/vinhos", summary="Dados de Importação de Vinhos")
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

@router.get("/uvas-frescas", summary="Dados de Importação de Uvas Frescas")
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

@router.get("/suco", summary="Dados de Importação de Suco de Uva")
async def get_juice_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre importação de suco de uva, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        logger.info(f"Fetching grape juice import data for year: {year}")
        data = scraper.get_juice_imports(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in juice imports endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de importação de suco de uva: {str(e)}"
        )

@router.get("/espumantes", summary="Dados de Importação de Espumantes")
async def get_sparkling_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre importação de espumantes, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ImportsScraper()
        logger.info(f"Fetching sparkling wine import data for year: {year}")
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

@router.get("/passas", summary="Dados de Importação de Uvas Passas")
async def get_raisins_import_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre importação de uvas passas, com possibilidade de filtrar por ano.
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
            detail=f"Erro ao obter dados de importação de uvas passas: {str(e)}"
        )
