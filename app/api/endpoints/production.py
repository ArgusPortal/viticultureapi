from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from app.scraper.base_scraper import BaseScraper
import pandas as pd
import logging
import os
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

router = APIRouter()

class ProductionScraper(BaseScraper):
    def get_general_production(self, year=None):
        """Obtém dados gerais de produção vitivinícola"""
        params = {
            'opcao': 'opt_02',
            'subopcao': 'subopt_00'
        }
        
        if year:
            params['ano'] = year
            
        # Try web scraping first
        soup = self._get_soup(self.BASE_URL, params)
        df = self._extract_table_data(soup)
        
        # If web scraping fails or returns empty data, try CSV fallback
        if df.empty:
            logger.warning("Web scraping returned empty data, trying CSV fallback")
            fallback_data = self._fallback_to_csv('production', None, year)
            if fallback_data and fallback_data.get("data"):
                logger.info("Successfully loaded data from CSV fallback")
                return fallback_data
        
        # Limpar e converter dados se necessário
        if not df.empty and 'Quantidade' in df.columns:
            df['Quantidade'] = df['Quantidade'].str.replace('.', '')
            df['Quantidade'] = df['Quantidade'].str.replace(',', '.').astype(float)
        
        # Return a consistent format
        return {
            "data": df.to_dict('records') if not df.empty else [], 
            "source_url": self._get_source_url(params),
            "source": "web_scraping"
        }
    
    def get_wine_production(self, year=None):
        """Obtém dados específicos de produção de vinhos"""
        params = {
            'opcao': 'opt_02',
            'subopcao': 'subopt_01'  # Subopcao para vinhos
        }
        
        if year:
            params['ano'] = year
            
        soup = self._get_soup(self.BASE_URL, params)
        df = self._extract_table_data(soup)
        
        # If web scraping fails, try CSV fallback
        if df.empty:
            logger.warning("Web scraping returned empty data for wine production, trying CSV fallback")
            fallback_data = self._fallback_to_csv('production', 'wine', year)
            if fallback_data and fallback_data.get("data"):
                logger.info("Successfully loaded wine data from CSV fallback")
                return fallback_data
        
        # Processar dados se necessário
        if not df.empty and 'Quantidade' in df.columns:
            df['Quantidade'] = df['Quantidade'].str.replace('.', '')
            df['Quantidade'] = df['Quantidade'].str.replace(',', '.').astype(float)
            
        return {
            "data": df.to_dict('records') if not df.empty else [],
            "source_url": self._get_source_url(params),
            "source": "web_scraping"
        }
    
    def get_grape_production(self, year=None):
        """Obtém dados específicos de produção de uvas"""
        params = {
            'opcao': 'opt_02',
            'subopcao': 'subopt_02'  # Subopcao para uvas
        }
        
        if year:
            params['ano'] = year
            
        soup = self._get_soup(self.BASE_URL, params)
        df = self._extract_table_data(soup)
        
        # If web scraping fails, try CSV fallback
        if df.empty:
            logger.warning("Web scraping returned empty data for grape production, trying CSV fallback")
            fallback_data = self._fallback_to_csv('production', 'grape', year)
            if fallback_data and fallback_data.get("data"):
                logger.info("Successfully loaded grape data from CSV fallback")
                return fallback_data
        
        # Processar dados se necessário
        if not df.empty and 'Quantidade' in df.columns:
            df['Quantidade'] = df['Quantidade'].str.replace('.', '')
            df['Quantidade'] = df['Quantidade'].str.replace(',', '.').astype(float)
            
        return {
            "data": df.to_dict('records') if not df.empty else [],
            "source_url": self._get_source_url(params),
            "source": "web_scraping"
        }
    
    def _get_source_url(self, params):
        """Helper to generate the source URL for debugging"""
        return f"{self.BASE_URL}?{urlencode(params)}"

    def _fallback_to_csv(self, category, subcategory=None, year=None):
        """
        Fallback to load data from local CSV files when web scraping fails.
        
        Args:
            category (str): Data category (e.g., 'production', 'processing')
            subcategory (str, optional): Data subcategory
            year (int, optional): Year to filter data
            
        Returns:
            dict: Loaded data
        """
        try:
            # Map API categories to CSV filenames
            filename_mapping = {
                'production': {
                    None: 'Producao.csv',
                    'wine': 'Producao.csv',  # Filter for wine data
                    'grape': 'Producao.csv',  # Filter for grape data
                }
            }
            
            # Try to find the appropriate CSV file
            if category in filename_mapping and subcategory in filename_mapping[category]:
                filename = filename_mapping[category][subcategory]
                file_path = os.path.join(self.DATA_DIR, filename)
                
                if os.path.exists(file_path):
                    logger.info(f"Loading data from CSV file: {file_path}")
                    df = pd.read_csv(file_path)
                    
                    # Filter by year if provided
                    if year is not None and 'Ano' in df.columns:
                        df = df[df['Ano'] == year]
                    
                    # Return in the same format as web scraping
                    return {"data": df.to_dict('records'), "source": "local_csv"}
                else:
                    logger.warning(f"CSV file not found: {file_path}")
            else:
                logger.warning(f"No CSV mapping for category: {category}, subcategory: {subcategory}")
                
            return {"data": [], "source": "local_csv_not_found"}
        except Exception as e:
            logger.error(f"Error loading CSV data: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e)}

@router.get("/", summary="Dados gerais de produção")
async def get_production_data(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados gerais sobre a produção vitivinícola, com possibilidade de filtrar por ano.
    Dados obtidos do arquivo Producao.csv ou diretamente do site VitiBrasil.
    """
    try:
        scraper = ProductionScraper()
        logger.info(f"Fetching production data for year: {year}")
        data = scraper.get_general_production(year)
        
        if data is None:
            logger.warning(f"No data returned for year {year}")
            raise HTTPException(
                status_code=404, 
                detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
            )
            
        # Check if data is empty (previously this was inconsistent with the return format)
        if isinstance(data, dict) and (
            "error" in data or 
            not data.get("data") or 
            (isinstance(data.get("data"), list) and len(data.get("data", [])) == 0)
        ):
            logger.warning(f"Empty data returned for year {year}")
            raise HTTPException(
                status_code=404, 
                detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
            )
            
        # Return consistent format
        return {
            "data": data.get("data", []),
            "total": len(data.get("data", [])),
            "ano": year,
            "source_url": data.get("source_url", ""),
            "source": data.get("source", "unknown")
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in production endpoint: {error_details}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de produção: {str(e)}"
        )

@router.get("/wine", summary="Dados de produção de vinhos")
async def get_wine_production(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre a produção de vinhos, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProductionScraper()
        logger.info(f"Fetching wine production data for year: {year}")
        data = scraper.get_wine_production(year)
        
        if data is None or (isinstance(data, pd.DataFrame) and data.empty) or (
            isinstance(data, dict) and ("error" in data or not data.get("data"))
        ):
            logger.warning(f"No wine data found for year {year}")
            raise HTTPException(
                status_code=404, 
                detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
            )
            
        return {
            "data": data.get("data", []),
            "total": len(data.get("data", [])),
            "ano": year,
            "source": data.get("source", "unknown"),
            "source_url": data.get("source_url", "")
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in wine production endpoint: {error_details}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de produção de vinhos: {str(e)}"
        )

@router.get("/grape", summary="Dados de produção de uvas")
async def get_grape_production(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre a produção de uvas, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProductionScraper()
        logger.info(f"Fetching grape production data for year: {year}")
        data = scraper.get_grape_production(year)
        
        if data is None or (isinstance(data, dict) and "error" in data) or (
            isinstance(data, pd.DataFrame) and data.empty
        ):
            logger.warning(f"No grape data found for year {year}")
            raise HTTPException(
                status_code=404, 
                detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
            )
            
        return {
            "data": data.get("data", []),
            "total": len(data.get("data", [])),
            "ano": year,
            "source": data.get("source", "unknown"),
            "source_url": data.get("source_url", "")
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in grape production endpoint: {error_details}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de produção de uvas: {str(e)}"
        )
