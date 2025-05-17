from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional
from app.scraper.processing_scraper import ProcessingScraper
from app.core.security import verify_token
from app.core.hypermedia import add_links  # Add this import
import logging
import traceback
from enum import Enum
from pydantic import BaseModel, Field
from app.core.cache import cache_result  # Add missing import for cache_result

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/processing",
    tags=["Processamento"],
    responses={
        404: {"description": "Dados não encontrados"},
        500: {"description": "Erro no servidor"}
    },
)


class GrapeCategory(str, Enum):
    """Categorias de uvas disponíveis"""
    vinifera = "vinifera"
    american = "american"
    table = "table"
    unclassified = "unclassified"

def build_api_response(data, year=None):
    """Build standardized API response from scraped data"""
    if not data or not isinstance(data, dict):
        logger.warning("Invalid data format received")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
        )
        
    if "error" in data:
        logger.error(f"Error in scraped data: {data['error']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dados: {data['error']}"
        )
        
    if not data.get("data") or len(data.get("data", [])) == 0:
        logger.warning(f"No data returned for year {year}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
        )
    
    response = {
        "data": data.get("data", []),
        "total": len(data.get("data", [])),
        "ano_filtro": year,
        "source_url": data.get("source_url", ""),
        "source": data.get("source", "unknown")
    }
    
    # Add HATEOAS links to the response
    return add_links(response, "processing", year)

@router.get("/", 
    summary="Dados gerais de processamento", 
    response_description="Dados combinados de processamento de uvas de todas as categorias")
async def get_processing_data(
    year: Optional[int] = Query(None, 
                              description="Ano de referência dos dados", 
                              example=2022,
                              ge=1970, 
                              le=2023),
    current_user: str = Depends(verify_token)
):
    """
    Retorna dados agregados de processamento de uvas de todas as categorias.
    
    ## Descrição
    
    Este endpoint combina dados de processamento de todos os tipos de uvas disponíveis no site VitiBrasil,
    incluindo viníferas, americanas/híbridas, uvas de mesa e sem classificação. É útil para obter uma
    visão geral completa do processamento de uvas no Brasil.
    
    ## Categorias incluídas
    
    - **Viníferas**: Uvas de variedades europeias utilizadas principalmente para vinhos finos
    - **Americanas e híbridas**: Variedades mais resistentes, usadas para vinhos de mesa e sucos
    - **Uvas de mesa**: Variedades destinadas ao consumo in natura
    - **Sem classificação**: Uvas sem categoria definida no sistema
    
    ## Parâmetros
    
    - **year**: Opcional. Filtra os dados para mostrar apenas o ano especificado.
                Se não for fornecido, retorna dados de todos os anos disponíveis.
    
    ## Notas
    
    Cada registro inclui um campo 'categoria' que identifica de qual tipo de uva o registro se origina,
    permitindo análises mais detalhadas dos dados combinados.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching combined processing data for year: {year} - requested by user: {current_user}")
        data = scraper.get_processing_data(year)
        
        # Use the standard response builder
        return build_api_response(data, year)
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"Error in processing endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro ao obter dados de processamento: {str(e)}"
        )

@router.get("/vinifera", 
    summary="Dados de processamento de uvas viníferas", 
    response_description="Dados de processamento de uvas viníferas")
@cache_result(ttl_seconds_or_func=3600)  # Nome de parâmetro corrigido
async def get_vinifera_processing_data(
    year: Optional[int] = Query(None, 
                              description="Ano de referência dos dados", 
                              example=2022,
                              ge=1970, 
                              le=2023),
    current_user: str = Depends(verify_token)
):
    """
    Retorna dados sobre o processamento de uvas viníferas, com possibilidade de filtrar por ano.
    
    ## Descrição
    
    As uvas viníferas (Vitis vinifera) são variedades de origem europeia utilizadas principalmente 
    na produção de vinhos finos. Este endpoint fornece dados sobre o processamento industrial 
    dessas variedades no Brasil.
    
    ## Parâmetros
    
    - **year**: Opcional. Filtra os dados para mostrar apenas o ano especificado.
                Se não for fornecido, retorna dados de todos os anos disponíveis.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching vinifera grape processing data for year: {year} - requested by user: {current_user}")
        data = scraper.get_vinifera_processing(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in vinifera processing endpoint: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro ao obter dados de processamento de uvas viníferas: {str(e)}"
        )

@router.get("/american", 
    summary="Dados de processamento de uvas americanas e híbridas", 
    response_description="Dados de processamento de uvas americanas e híbridas")
@cache_result(ttl_seconds_or_func=3600)  # Nome de parâmetro corrigido
async def get_american_processing_data(
    year: Optional[int] = Query(None, 
                              description="Ano de referência dos dados", 
                              example=2022,
                              ge=1970, 
                              le=2023),
    current_user: str = Depends(verify_token)
):
    """
    Retorna dados sobre o processamento de uvas americanas e híbridas, com possibilidade de filtrar por ano.
    
    ## Descrição
    
    As uvas americanas (principalmente Vitis labrusca) e híbridas são variedades mais resistentes,
    amplamente utilizadas na produção de vinhos de mesa, sucos e outros derivados no Brasil.
    Este endpoint fornece dados específicos sobre o processamento dessas variedades.
    
    ## Parâmetros
    
    - **year**: Opcional. Filtra os dados para mostrar apenas o ano especificado.
                Se não for fornecido, retorna dados de todos os anos disponíveis.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching American grape processing data for year: {year} - requested by user: {current_user}")
        data = scraper.get_american_processing(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in American processing endpoint: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro ao obter dados de processamento de uvas americanas e híbridas: {str(e)}"
        )

@router.get("/table", 
    summary="Dados de processamento de uvas de mesa", 
    response_description="Dados de processamento de uvas de mesa")
async def get_table_processing_data(
    year: Optional[int] = Query(None, 
                              description="Ano de referência dos dados", 
                              example=2022,
                              ge=1970, 
                              le=2023),
    current_user: str = Depends(verify_token)
):
    """
    Retorna dados sobre o processamento de uvas de mesa, com possibilidade de filtrar por ano.
    
    ## Descrição
    
    As uvas de mesa são variedades destinadas principalmente ao consumo in natura (fresca),
    mas que eventualmente são processadas pela indústria. Este endpoint fornece dados
    sobre o processamento industrial dessas variedades.
    
    ## Parâmetros
    
    - **year**: Opcional. Filtra os dados para mostrar apenas o ano especificado.
                Se não for fornecido, retorna dados de todos os anos disponíveis.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching table grape processing data for year: {year} - requested by user: {current_user}")
        data = scraper.get_table_processing(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in table processing endpoint: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro ao obter dados de processamento de uvas de mesa: {str(e)}"
        )

@router.get("/unclassified", 
    summary="Dados de processamento de uvas sem classificação", 
    response_description="Dados de processamento de uvas sem classificação")
async def get_unclassified_processing_data(
    year: Optional[int] = Query(None, 
                              description="Ano de referência dos dados", 
                              example=2022,
                              ge=1970, 
                              le=2023),
    current_user: str = Depends(verify_token)
):
    """
    Retorna dados sobre o processamento de uvas sem classificação, com possibilidade de filtrar por ano.
    
    ## Descrição
    
    As uvas sem classificação são variedades que não estão categorizadas como viníferas,
    americanas/híbridas ou de mesa. Este endpoint fornece dados sobre o processamento
    dessas variedades não classificadas.
    
    ## Parâmetros
    
    - **year**: Opcional. Filtra os dados para mostrar apenas o ano especificado.
                Se não for fornecido, retorna dados de todos os anos disponíveis.
    """
    try:
        scraper = ProcessingScraper()
        logger.info(f"Fetching unclassified grape processing data for year: {year} - requested by user: {current_user}")
        data = scraper.get_unclassified_processing(year)
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in unclassified processing endpoint: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro ao obter dados de processamento de uvas sem classificação: {str(e)}"
        )
