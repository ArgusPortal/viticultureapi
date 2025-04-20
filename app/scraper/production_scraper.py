from .base_scraper import BaseScraper
import pandas as pd
import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductionScraper(BaseScraper):
    def get_wine_production(self, year=None):
        """Get wine production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_01'
            }
            result = self._get_production_data(params, 'wine', year)
            return result.get('data', []) if isinstance(result, dict) else []
        except Exception as e:
            logger.error(f"Error in wine production scraping: {str(e)}", exc_info=True)
            return []

    def get_grape_production(self, year=None):
        """Get grape production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_02'
            }
            result = self._get_production_data(params, 'grape', year)
            return result.get('data', []) if isinstance(result, dict) else []
        except Exception as e:
            logger.error(f"Error in grape production scraping: {str(e)}", exc_info=True)
            return []

    def get_derivative_production(self, year=None):
        """Get derivative production data for a specific year."""
        try:
            params = {
                'opcao': 'opt_02',
                'subopcao': 'subopt_03'
            }
            result = self._get_production_data(params, 'derivative', year)
            return result.get('data', []) if isinstance(result, dict) else []
        except Exception as e:
            logger.error(f"Error in derivative production scraping: {str(e)}", exc_info=True)
            return []

    def _get_source_url(self, params):
        """Helper to generate the source URL for debugging"""
        return f"{self.BASE_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    def _fetch_year_data(self, params, year, category_type=None):
        """Fetch data for a specific year."""
        try:
            # Clone params to avoid modifying the original
            year_params = params.copy()
            if year:
                year_params['ano'] = str(year)
                
            # Get HTML content
            soup = self._get_soup(self.BASE_URL, year_params)
            if not soup:
                return None
                
            # Extract table data
            df = self._extract_table_data(soup)
            
            if df.empty:
                return None
                
            # Clean quantity data
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
            category_type: Optional category filter
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
            # Validate year is within acceptable range
            current_year = datetime.now().year
            if not (self.MIN_YEAR <= year <= current_year):
                logger.warning(f"Year {year} is outside valid range ({self.MIN_YEAR}-{current_year})")
                # For future years, fallback to the most recent available year
                if year > current_year:
                    logger.info(f"Requested year {year} is in the future, trying current year {current_year}")
                    return self._get_production_data(params, category_type, current_year)
                return {"data": [], "source": "invalid_year", "source_url": source_url}
                
            # Try web scraping for the specific year
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
            years_with_data = 0
            
            logger.info(f"Fetching data for all {len(available_years)} available years")
            
            for yr in available_years:
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

    def _filter_data_by_category(self, data, category_type):
        """Filter data by category."""
        if not data or not category_type:
            return data
            
        # Define valid product categories
        valid_products = {
            'wine': [
                'Tinto', 'Branco', 'Rosado'
            ],
            'grape': [
                'Suco de uva integral', 'Suco de uva concentrado', 'Suco de uva adoçado',
                'Suco de uva orgânico', 'Suco de uva reconstituído'
            ],
            'derivative': [
                'Frisante', 'Vinho leve', 'Vinho licoroso', 'Vinho Composto', 
                'Vinho orgânico', 'Vinho acidificado', 
                'Espumante', 'Espumante moscatel', 'Base espumante', 'Base espumante moscatel',
                'Base Champenoise champanha', 'Base Charmat champanha'
            ]
        }
        
        # Define main category headers
        main_categories = {
            'wine': ['VINHOS'],
            'grape': ['SUCOS'],
            'derivative': ['DERIVADOS', 'ESPUMANTES', 'OUTROS']
        }
        
        filtered_data = []
        
        for item in data:
            # Skip if no product field
            product = item.get('Produto', '')
            if not product:
                continue
                
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
