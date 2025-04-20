from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any, Union
from app.scraper.base_scraper import BaseScraper
import pandas as pd
import logging
import os
from urllib.parse import urlencode
import re
from datetime import datetime
import requests
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

class ProductionScraper(BaseScraper):
    def _safe_soup_find_all(self, soup, *args, **kwargs):
        """Safely call find_all on a soup object with error handling"""
        try:
            if soup is None:
                return []
            return soup.find_all(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in soup.find_all: {str(e)}")
            return []

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
        text_blocks = self._safe_soup_find_all(soup, ['p', 'div', 'span'])
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

    def _get_fallback_years(self):
        """Return a fixed range of years based on the known data range (1970-2023)"""
        # Define the actual range of years covered in the database
        # This prevents returning non-existent future years or limiting to only recent years
        min_year = 1970
        max_year = 2023  # Set max year to the known last year in the dataset
        
        fallback_years = list(range(min_year, max_year + 1))
        logger.info(f"Using complete year range from {min_year} to {max_year}")
        return sorted(fallback_years, reverse=True)  # Return in descending order (newest first)

    def _extract_years_from_text(self, soup):
        """Extract years from text content in the soup"""
        if not soup:
            return set()
            
        # Look for years within the valid range (1970-2023)
        year_pattern = re.compile(r'\b(19[7-9]\d|20[0-1]\d|202[0-3])\b')  # Match years 1970-2023
        years = set()
        
        try:
            for text in soup.stripped_strings:
                matches = year_pattern.findall(text)
                for match in matches:
                    try:
                        year = int(match)
                        # Ensure year is within valid range
                        if 1970 <= year <= 2023:
                            years.add(year)
                    except ValueError:
                        continue
            
            if years:
                logger.info(f"Inferred {len(years)} available years: {sorted(years, reverse=True)}")
        except Exception as e:
            logger.error(f"Error extracting years from text: {str(e)}")
        
        return years

    def _get_available_years(self):
        """
        Get a list of all available years from the site.
        This helps us fetch data for all years when no specific year is requested.
        """
        try:
            # Try to get years from main page
            soup = self._get_soup(self.BASE_URL)
            if not soup:
                logger.warning("Failed to get soup for available years")
                return self._get_fallback_years()
                
            # Simple, direct approach to extract years
            years = []
            
            # Method 1: Try to find the year dropdown
            year_select = soup.find('select', {'name': 'ano'})
            if year_select:
                # Safer way to check for options
                try:
                    # Get all option elements directly using regex
                    option_elements = self._safe_soup_find_all(soup, 'option')
                    if option_elements:
                        for option in option_elements:
                            year_text = option.text.strip() if hasattr(option, 'text') else ""
                            if year_text.isdigit():
                                try:
                                    year = int(year_text)
                                    # Ensure year is within valid range
                                    if 1970 <= year <= 2023:
                                        years.append(year)
                                except ValueError:
                                    continue
                except Exception as e:
                    logger.warning(f"Error extracting years from dropdown: {str(e)}")
            
            # Method 2: Extract years from any text in the page
            if not years:
                years = self._extract_years_from_text(soup)
            
            # If we found years, return them, otherwise use fallback
            if years:
                return sorted(list(years), reverse=True)
            else:
                return self._get_fallback_years()
                
        except Exception as e:
            logger.error(f"Error getting available years: {str(e)}")
            return self._get_fallback_years()

    def _fetch_year_data(self, params, year, category_type=None):
        """
        Fetch data for a specific year.
        
        Args:
            params: Request parameters
            year: Year to fetch
            category_type: Optional category filter ('wine', 'grape', 'derivative')
            
        Returns:
            List of record dictionaries or None on error
        """
        try:
            year_params = params.copy()
            if year is not None:
                year_params['ano'] = year
            
            soup = self._get_soup(self.BASE_URL, year_params)
            if not soup:
                logger.warning(f"Failed to get soup for year {year}")
                return None
                
            df = self._extract_table_data(soup)
            
            if df.empty:
                logger.warning(f"Empty dataframe for year {year}")
                return None
            
            # Clean and convert data
            try:
                if 'Quantidade' in df.columns:
                    df['Quantidade'] = df['Quantidade'].astype(str).str.replace('.', '')
                    df['Quantidade'] = df['Quantidade'].astype(str).str.replace(',', '.').astype(float)
                elif 'Quantidade (L.)' in df.columns:
                    df['Quantidade'] = df['Quantidade (L.)'].astype(str).str.replace('.', '')
                    df['Quantidade'] = df['Quantidade'].astype(str).str.replace(',', '.').astype(float)
            except Exception as e:
                logger.warning(f"Error cleaning quantity data: {str(e)}")
            
            # Convert to records
            records = df.to_dict('records')
            
            # Filter by category if needed
            if category_type and records:
                records = self._filter_data_by_category(records, category_type)
            
            # Add year to each record if year isn't already present
            if records:
                for record in records:
                    if 'Ano' not in record or not record['Ano']:
                        record['Ano'] = year
            
            return records
        except Exception as e:
            logger.error(f"Error in _fetch_year_data for year {year}: {str(e)}", exc_info=True)
            return None

    def _get_production_data(self, params, category_type=None, year=None):
        """
        Generic method to fetch production data.
        
        Args:
            params: Request parameters
            category_type: Optional category filter ('wine', 'grape', 'derivative')
            year: Optional year filter
            
        Returns:
            Dict with fetched data
        """
        # Create source URL for debugging
        source_url = self._get_source_url(params)
        
        # Try CSV fallback first, especially for multi-year queries
        if not year:
            fallback_data = self._fallback_to_csv('production', category_type, None)
            if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                logger.info(f"Successfully loaded multi-year {category_type or 'general'} data from CSV")
                return fallback_data
        
        # If specific year is requested or CSV fallback failed
        if year:
            # Try web scraping first for the specific year
            records = self._fetch_year_data(params, year, category_type)
            
            # If web scraping fails, try CSV fallback for that year
            if not records:
                logger.warning(f"Web scraping returned empty data for {category_type or 'general'} "
                              f"for year {year}, trying CSV fallback")
                fallback_data = self._fallback_to_csv('production', category_type, year)
                if fallback_data and fallback_data.get("data"):
                    logger.info(f"Successfully loaded {category_type or 'general'} data for year {year} from CSV fallback")
                    return fallback_data
                
                # If even CSV fallback failed, return empty result
                return {"data": [], "source": "no_data_found", "source_url": source_url}
            
            # Web scraping successful
            return {
                "data": records,
                "source": "web_scraping",
                "source_url": source_url
            }
        else:
            # For multi-year requests where CSV failed, try web scraping for multiple years
            available_years = self._get_available_years()
            if not available_years:
                logger.warning(f"Could not determine available years for {category_type or 'general'} data")
                # Try web scraping without year parameter
                records = self._fetch_year_data(params, None, category_type)
                
                return {
                    "data": records or [],
                    "source": "web_scraping",
                    "source_url": source_url
                }
            
            # Fetch data for each available year and combine
            all_data = []
            # No limit on years - get all available years
            years_with_data = 0
            
            logger.info(f"Fetching data for all {len(available_years)} available years")
            
            for yr in available_years:  # Removed the limit to get all years
                try:
                    records = self._fetch_year_data(params, yr, category_type)
                    if records:
                        all_data.extend(records)
                        years_with_data += 1
                        logger.info(f"Added {len(records)} {category_type or 'general'} records for year {yr}")
                except Exception as e:
                    logger.error(f"Error fetching {category_type or 'general'} data for year {yr}: {str(e)}")
            
            logger.info(f"Retrieved data for {years_with_data} out of {len(available_years)} years attempted")
            
            return {
                "data": all_data,
                "source": "web_scraping_multi_year",
                "source_url": source_url
            }

    def get_general_production(self, year=None):
        """Obtém dados gerais de produção vitivinícola"""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_00'
            }
            return self._get_production_data(params, None, year)
        except Exception as e:
            logger.error(f"Error in general production scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_wine_production(self, year=None):
        """Get wine production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_01'
            }
            return self._get_production_data(params, 'wine', year)
        except Exception as e:
            logger.error(f"Error in wine production scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_grape_production(self, year=None):
        """Get grape production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_02'
            }
            return self._get_production_data(params, 'grape', year)
        except Exception as e:
            logger.error(f"Error in grape production scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_derivative_production(self, year=None):
        """Get derivative production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_03'
            }
            return self._get_production_data(params, 'derivative', year)
        except Exception as e:
            logger.error(f"Error in derivative production scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}

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

# Create unified response handling for all endpoints
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
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
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
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
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
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
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
        return build_api_response(data, year)
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in derivative production endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter dados de produção de derivados: {str(e)}"
        )
