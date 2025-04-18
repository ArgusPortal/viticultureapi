from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from app.scraper.base_scraper import BaseScraper
import pandas as pd
import logging
import os
from urllib.parse import urlencode
import re
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

class ProductionScraper(BaseScraper):
    def _extract_current_year_from_page(self, soup):
        """
        Attempt to extract the current year from the page content.
        If not found, defaults to the current year.
        """
        if not soup:
            return None
            
        # Try to find year in page title or headers
        title_element = soup.find('title')
        header_elements = [soup.find('h1'), soup.find('h2'), soup.find('h3')]
        
        elements_to_check = [title_element] + header_elements
        for element in elements_to_check:
            if element and element.text:
                year_match = re.search(r'20\d{2}', element.text)
                if year_match:
                    try:
                        return int(year_match.group(0))
                    except ValueError:
                        continue
        
        # If we couldn't find a year, check for any text that might contain a year
        text_blocks = soup.find_all(['p', 'div', 'span'])
        for block in text_blocks:
            if block and block.text:
                year_match = re.search(r'20\d{2}', block.text)
                if year_match:
                    try:
                        return int(year_match.group(0))
                    except ValueError:
                        continue
        
        # If we still can't find the year, use the current year as a last resort
        return datetime.now().year

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
        
        # Extract current year if not specified
        current_year = year or self._extract_current_year_from_page(soup)
        
        # Limpar e converter dados se necessário
        if not df.empty and 'Quantidade' in df.columns:
            df['Quantidade'] = df['Quantidade'].str.replace('.', '')
            df['Quantidade'] = df['Quantidade'].str.replace(',', '.').astype(float)
            
            # Add year information to each record
            if current_year:
                for record in df.to_dict('records'):
                    record['Ano'] = current_year
        
        # Return a consistent format
        return {
            "data": df.to_dict('records') if not df.empty else [], 
            "source_url": self._get_source_url(params),
            "source": "web_scraping"
        }
    
    def get_wine_production(self, year=None):
        """Get wine production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_01'
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
            
            # Filter the data to include only wine categories
            filtered_data = self._filter_data_by_category(df.to_dict('records'), category_type='wine')
            
            # Get the current year from the page if not specified
            current_year = year or self._extract_current_year_from_page(soup)
            
            # Add year information to each data item
            if current_year:
                for item in filtered_data:
                    item['Ano'] = current_year
            
            return {
                "data": filtered_data,
                "source": "web_scraping",
                "source_url": self._get_source_url(params)
            }
        except Exception as e:
            logger.error(f"Error in wine production scraping: {str(e)}")
            return {"data": [], "error": str(e)}
    
    def get_grape_production(self, year=None):
        """Get grape production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_02'
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
            
            # Filter the data to include only grape categories
            filtered_data = self._filter_data_by_category(df.to_dict('records'), category_type='grape')
            
            # Get the current year from the page if not specified
            current_year = year or self._extract_current_year_from_page(soup)
            
            # Add year information to each data item
            if current_year:
                for item in filtered_data:
                    item['Ano'] = current_year
            
            return {
                "data": filtered_data,
                "source": "web_scraping",
                "source_url": self._get_source_url(params)
            }
        except Exception as e:
            logger.error(f"Error in grape production scraping: {str(e)}")
            return {"data": [], "error": str(e)}
    
    def get_derivative_production(self, year=None):
        """Get derivative production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_03'
            }
            
            if year:
                params['ano'] = year
                
            soup = self._get_soup(self.BASE_URL, params)
            df = self._extract_table_data(soup)
            
            # If web scraping fails, try CSV fallback
            if df.empty:
                logger.warning("Web scraping returned empty data for derivative production, trying CSV fallback")
                fallback_data = self._fallback_to_csv('production', 'derivative', year)
                if fallback_data and fallback_data.get("data"):
                    logger.info("Successfully loaded derivative data from CSV fallback")
                    return fallback_data
            
            # Filter the data to include only derivative categories
            filtered_data = self._filter_data_by_category(df.to_dict('records'), category_type='derivative')
            
            # Get the current year from the page if not specified
            current_year = year or self._extract_current_year_from_page(soup)
            
            # Add year information to each data item
            if current_year:
                for item in filtered_data:
                    item['Ano'] = current_year
            
            return {
                "data": filtered_data,
                "source": "web_scraping",
                "source_url": self._get_source_url(params)
            }
        except Exception as e:
            logger.error(f"Error in derivative production scraping: {str(e)}")
            return {"data": [], "error": str(e)}
    
    def _filter_data_by_category(self, data, category_type):
        """
        Filter production data by category type.
        
        Args:
            data: Production data to filter
            category_type: 'wine', 'grape', or 'derivative'
            
        Returns:
            List of filtered data entries
        """
        if not data:
            return []
        
        # Define prefixes for different categories
        prefixes = {
            'wine': ['vm_', 'vf_'],      # Wine prefixes (vinho de mesa, vinho fino)
            'grape': ['su_'],            # Juice prefixes (sucos)
            'derivative': ['de_']        # Derivative prefixes
        }
        
        # Define main categories for classification
        main_categories = {
            'wine': ['VINHO DE MESA', 'VINHO FINO DE MESA', 'VINIFERA'],
            'grape': ['SUCO'], 
            'derivative': ['DERIVADOS']
        }
        
        # Define valid product types for each category
        valid_products = {
            'wine': [
                'Tinto', 'Branco', 'Rosado'  # Only these are valid wine types
            ],
            'grape': [
                'Suco de uva integral', 'Suco de uva concentrado', 'Suco de uva adoçado',
                'Suco de uva orgânico', 'Suco de uva reconstituído'
            ],
            'derivative': [
                'Frisante', 'Vinho leve', 'Vinho licoroso', 'Vinho Composto', 
                'Vinho orgânico', 'Vinho acidificado', 
                'Espumante', 'Espumante moscatel', 'Base espumante', 'Base espumante moscatel',
                'Base Champenoise champanha', 'Base Charmat champanha',
                'Bebida de uva', 'Polpa de uva', 'Mosto', 'Mosto simples', 'Mosto concentrado',
                'Mosto de uva com bagaço', 'Mosto dessulfitado', 'Mosto parcialmente fermentado',
                'Destilado', 'Bagaceira', 'Vinagre', 'Borra', 'Borra seca', 'Borra líquida',
                'Pisco', 'Licorosos', 'Compostos', 'Jeropiga', 'Filtrado', 'Mistelas',
                'Néctar de uva', 'Outros derivados',
                'Destilado alcoólico simples de bagaceira', 'Licor de bagaceira',
                'Brandy'
            ]
        }
        
        # Filter the data based on category
        filtered_data = []
        for item in data:
            product = item.get('Produto', '')
            
            # Check if this is a main category header
            if any(cat in product.upper() for cat in main_categories['wine']):
                if category_type == 'wine':
                    filtered_data.append(item)
                continue
            elif any(cat in product.upper() for cat in main_categories['grape']):
                if category_type == 'grape':
                    filtered_data.append(item)
                continue
            elif any(cat in product.upper() for cat in main_categories['derivative']):
                if category_type == 'derivative':
                    filtered_data.append(item)
                continue
            
            # Now check if the product belongs to wine category
            if category_type == 'wine':
                if product in valid_products['wine'] or product.strip() in valid_products['wine']:
                    filtered_data.append(item)
            
            # Check if product belongs to grape category
            elif category_type == 'grape':
                if product in valid_products['grape'] or product.strip() in valid_products['grape']:
                    filtered_data.append(item)
            
            # Check if product belongs to derivative category
            elif category_type == 'derivative':
                if any(product.startswith(deriv) or product == deriv for deriv in valid_products['derivative']):
                    filtered_data.append(item)
        
        return filtered_data

    def _get_source_url(self, params):
        """Helper to generate the source URL for debugging"""
        return f"{self.BASE_URL}?{urlencode(params)}"

    def _fallback_to_csv(self, category, subcategory=None, year=None):
        """
        Fallback to load data from local CSV files when web scraping fails.
        """
        try:
            # Map API categories to CSV filenames
            csv_files = {
                'production': {
                    None: 'Producao.csv',
                    'wine': 'Producao.csv',      # Filter for wine data
                    'grape': 'Producao.csv',     # Filter for grape/juice data
                    'derivative': 'Producao.csv' # Filter for derivative data
                },
            }
            
            # Try to find the appropriate CSV file
            if category in csv_files and subcategory in csv_files[category]:
                filename = csv_files[category][subcategory]
                file_path = os.path.join(self.DATA_DIR, filename)
                
                if os.path.exists(file_path):
                    logger.info(f"Loading data from CSV file: {file_path}")
                    df = pd.read_csv(file_path, sep=';')
                    
                    # Check if years are in columns (1970, 1971, etc.)
                    year_columns = [col for col in df.columns if str(col).isdigit() or 
                                   (isinstance(col, str) and col.isdigit())]
                    
                    # If we have year columns and no specific year filter
                    if year_columns and year is None:
                        # We need to reshape the data to include the year in each record
                        logger.info("Reshaping data to include year information")
                        
                        # Keep only the necessary columns for identification
                        id_columns = ['id', 'control', 'produto']
                        id_columns = [col for col in id_columns if col in df.columns]
                        
                        # Melt the DataFrame to convert from wide to long format
                        melted_df = pd.melt(
                            df,
                            id_vars=id_columns,
                            value_vars=year_columns,
                            var_name='Ano',
                            value_name='Quantidade_Numerica'
                        )
                        
                        # Convert Ano to int
                        melted_df['Ano'] = melted_df['Ano'].astype(int)
                        
                        # Rename 'produto' to 'Produto' if it exists
                        if 'produto' in melted_df.columns:
                            melted_df = melted_df.rename(columns={'produto': 'Produto'})
                        
                        # Format the quantity as string with thousand separator
                        melted_df['Quantidade'] = melted_df['Quantidade_Numerica'].apply(
                            lambda x: f"{int(x):,}".replace(',', '.') if pd.notna(x) and x != 0 else "0"
                        )
                        
                        # Filter out zero or null quantities
                        melted_df = melted_df[melted_df['Quantidade_Numerica'] > 0]
                        
                        # Use the transformed DataFrame
                        df = melted_df
                    elif year is not None:
                        # If specific year is requested, filter the data
                        if 'Ano' in df.columns:
                            df = df[df['Ano'] == year]
                        elif str(year) in df.columns:
                            # If year is a column, reshape to have only that year's data
                            id_columns = [col for col in df.columns if col != str(year) and not str(col).isdigit()]
                            df = df[id_columns + [str(year)]].rename(columns={str(year): 'Quantidade_Numerica'})
                            df['Ano'] = year
                            df['Quantidade'] = df['Quantidade_Numerica'].apply(
                                lambda x: f"{int(x):,}".replace(',', '.') if pd.notna(x) and x != 0 else "0"
                            )
                            # Filter out zero or null quantities
                            df = df[df['Quantidade_Numerica'] > 0]
                    
                    # After loading the data, filter it based on the category if applicable
                    if subcategory in ['wine', 'grape', 'derivative'] and category == 'production':
                        filtered_data = self._filter_data_by_category(df.to_dict('records'), subcategory)
                        return {"data": filtered_data, "source": "local_csv"}
                    
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
        
        if data is None or (isinstance(data, dict) and "error" in data) or (
            not data.get("data") or 
            (isinstance(data.get("data"), list) and len(data.get("data", [])) == 0)
        ):
            logger.warning(f"No data returned for year {year}")
            raise HTTPException(
                status_code=404, 
                detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
            )
        
        return {
            "data": data.get("data", []),
            "total": len(data.get("data", [])),
            "ano_filtro": year,  # This is the year filter used
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
        
        if data is None or (isinstance(data, dict) and "error" in data) or (
            not data.get("data") or 
            (isinstance(data.get("data"), list) and len(data.get("data", [])) == 0)
        ):
            logger.warning(f"No wine data found for year {year}")
            raise HTTPException(
                status_code=404, 
                detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
            )
        
        return {
            "data": data.get("data", []),
            "total": len(data.get("data", [])),
            "ano_filtro": year,  # This is the year filter used
            "source_url": data.get("source_url", ""),
            "source": data.get("source", "unknown")
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
            not data.get("data") or 
            (isinstance(data.get("data"), list) and len(data.get("data", [])) == 0)
        ):
            logger.warning(f"No grape data found for year {year}")
            raise HTTPException(
                status_code=404, 
                detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
            )
        
        return {
            "data": data.get("data", []),
            "total": len(data.get("data", [])),
            "ano_filtro": year,  # This is the year filter used
            "source_url": data.get("source_url", ""),
            "source": data.get("source", "unknown")
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

@router.get("/derivative", summary="Dados de produção de derivados")
async def get_derivative_production(
    year: Optional[int] = Query(None, description="Ano de referência (ex: 2022)")
):
    """
    Retorna dados sobre a produção de derivados da uva e do vinho, com possibilidade de filtrar por ano.
    """
    try:
        scraper = ProductionScraper()
        logger.info(f"Fetching derivative production data for year: {year}")
        data = scraper.get_derivative_production(year)
        
        if data is None or (isinstance(data, dict) and "error" in data) or (
            not data.get("data") or 
            (isinstance(data.get("data"), list) and len(data.get("data", [])) == 0)
        ):
            logger.warning(f"No derivative data found for year {year}")
            raise HTTPException(
                status_code=404, 
                detail=f"Dados não encontrados para o ano {year if year else 'atual'}"
            )
        
        return {
            "data": data.get("data", []),
            "total": len(data.get("data", [])),
            "ano_filtro": year,  # This is the year filter used
            "source_url": data.get("source_url", ""),
            "source": data.get("source", "unknown")
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in derivative production endpoint: {error_details}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de produção de derivados: {str(e)}"
        )
