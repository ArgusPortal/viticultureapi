from app.scraper.base_scraper import BaseScraper
import pandas as pd
import logging
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup  # Add missing import

logger = logging.getLogger(__name__)

class ExportsScraper(BaseScraper):
    def get_exports_data(self, year=None):
        """
        Get exports data for a specific year or for all available years.
        
        Args:
            year: Optional year to filter data
            
        Returns:
            Dict with fetched data
        """
        try:
            params = {
                'opcao': 'opt_06',  # IMPORTANT: Exports option is opt_06
                'subopcao': 'subopt_00'  # All exports
            }
            
            return self._get_exports_data(params, None, year)
        except Exception as e:
            logger.error(f"Error in exports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_wine_exports(self, year=None):
        """Get table wine exports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_06',  # IMPORTANT: Exports option is opt_06
                'subopcao': 'subopt_01'  # Table wines exports
            }
            return self._get_exports_data(params, 'wine', year)
        except Exception as e:
            logger.error(f"Error in wine exports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_sparkling_exports(self, year=None):
        """Get sparkling wine exports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_06',  # IMPORTANT: Exports option is opt_06
                'subopcao': 'subopt_02'  # Sparkling exports
            }
            return self._get_exports_data(params, 'sparkling', year)
        except Exception as e:
            logger.error(f"Error in sparkling exports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_fresh_exports(self, year=None):
        """Get fresh grape exports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_06',  # IMPORTANT: Exports option is opt_06
                'subopcao': 'subopt_03'  # Fresh grape exports
            }
            return self._get_exports_data(params, 'fresh', year)
        except Exception as e:
            logger.error(f"Error in fresh grape exports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_juice_exports(self, year=None):
        """Get juice exports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_06',  # IMPORTANT: Exports option is opt_06
                'subopcao': 'subopt_04'  # Juice exports
            }
            return self._get_exports_data(params, 'juice', year)
        except Exception as e:
            logger.error(f"Error in juice exports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def _get_exports_data(self, params, category_type=None, year=None):
        """
        Generic method to fetch exports data.
        
        Args:
            params: Request parameters
            category_type: Optional category filter
            year: Optional year filter
            
        Returns:
            Dict with fetched data
        """
        # Create source URL for debugging
        source_url = f"{self.BASE_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        
        # Try CSV fallback first, especially for multi-year queries
        if not year:
            fallback_data = self._fallback_to_csv('exports', category_type, None)
            if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                logger.info(f"Successfully loaded multi-year {category_type or 'general'} exports data from CSV")
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
                    # Recursive call with current year
                    new_params = params.copy()
                    return self._get_exports_data(new_params, category_type, current_year)
                return {"data": [], "source": "invalid_year", "source_url": source_url}
                
            # Try web scraping for the specific year
            year_params = params.copy()
            year_params['ano'] = str(year)  # Convert to string for consistency
            
            soup = self._get_soup(self.BASE_URL, year_params)
            if not soup:
                logger.warning(f"Failed to get exports data for year {year}")
                
                # Try with optional parameter encoding
                try:
                    # Some sites need special URL encoding for parameters
                    encoded_params = "&".join([f"{k}={v}" for k, v in year_params.items()])
                    url_with_params = f"{self.BASE_URL}?{encoded_params}"
                    logger.info(f"Trying alternative URL encoding: {url_with_params}")
                    
                    response = self.session.get(url_with_params, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        logger.info("Successfully got response with alternative URL encoding")
                    else:
                        logger.warning(f"Alternative URL encoding failed with status {response.status_code}")
                        soup = None
                except Exception as e:
                    logger.error(f"Error with alternative URL encoding: {str(e)}")
                    soup = None
                
                # If still no success, try CSV fallback for that year
                if not soup:
                    fallback_data = self._fallback_to_csv('exports', category_type, year)
                    if fallback_data and fallback_data.get("data"):
                        logger.info(f"Successfully loaded {category_type or 'general'} exports data for year {year} from CSV")
                        return fallback_data
                    
                    # If all else fails, try the official VitiBrasil Excel files for recent years
                    if year >= 2015:
                        logger.info(f"Trying Excel data sources for year {year}")
                        excel_data = self._try_excel_source(category_type, year)
                        if excel_data and excel_data.get("data"):
                            return excel_data
                    
                    return {"data": [], "source": "no_data_found", "source_url": source_url}
            
            # Extract table data
            df = self._extract_table_data(soup)
            
            if df.empty:
                logger.warning(f"No exports data found for year {year}")
                
                # If the primary extraction fails, try a more focused approach
                data_tables = self._safe_find_all(soup, 'table')
                
                if data_tables:
                    logger.info(f"Trying focused extraction on {len(data_tables)} tables")
                    
                    for i, table in enumerate(data_tables):
                        try:
                            # Skip small tables (likely navigation)
                            rows = self._safe_find_all(table, 'tr') if table else []
                            if len(rows) < 3:
                                continue
                                
                            # Look for country names which are strong indicators of import/export tables
                            countries = ['argentina', 'chile', 'uruguai', 'alemanha', 'itália', 'portugal', 'frança']
                            table_text = table.get_text().lower() if table else ""
                            if any(country in table_text for country in countries):
                                logger.info(f"Table {i} contains country names, attempting extraction")
                                
                                # Try to create a dataframe with country data
                                rows = []
                                for tr in self._safe_find_all(table, 'tr'):
                                    if not tr:
                                        continue
                                    
                                    td_cells = self._safe_find_all(tr, ['td', 'th'])
                                    if not td_cells:
                                        continue
                                        
                                    cells = [td.get_text(strip=True) if td else "" for td in td_cells]
                                    if cells and len(cells) >= 2:  # Need at least country and one value
                                        # Skip header/footer/navigation rows
                                        if any(c.lower() in ['download', 'topo', 'voltar'] for c in cells if c):
                                            continue
                                        rows.append(cells)
                                
                                # Determine number of columns based on most common row length
                                from collections import Counter
                                col_counts = Counter([len(r) for r in rows])
                                most_common_cols = col_counts.most_common(1)[0][0]
                                
                                # Create headers based on column content
                                if most_common_cols == 2:
                                    headers = ['País', 'Quantidade (Kg)']
                                elif most_common_cols == 3:
                                    headers = ['País', 'Quantidade (Kg)', 'Valor (US$)']
                                else:
                                    headers = [f"Column{i+1}" for i in range(most_common_cols)]
                                
                                # Create dataframe
                                table_df = pd.DataFrame([r[:most_common_cols] for r in rows if len(r) >= most_common_cols], columns=headers)
                                
                                if not table_df.empty:
                                    df = table_df
                                    logger.info(f"Successfully extracted {len(df)} rows with focused method")
                                    break
                        except Exception as e:
                            logger.error(f"Error in focused extraction for table {i}: {str(e)}")
                
                # If still empty, try CSV fallback as a last resort
                if df.empty:
                    fallback_data = self._fallback_to_csv('exports', category_type, year)
                    if fallback_data and fallback_data.get("data"):
                        logger.info(f"Successfully loaded {category_type or 'general'} exports data from CSV after web extraction failed")
                        return fallback_data
                    return {"data": [], "source": "empty_data", "source_url": source_url}
            
            # Process data
            records = df.to_dict('records')
            
            # Filter out unwanted header and footer rows
            records = self._filter_unwanted_rows(records)
            
            # Add year to records if not present
            for record in records:
                if 'Ano' not in record or not record['Ano']:
                    record['Ano'] = year
            
            return {
                "data": records,
                "source": "web_scraping",
                "source_url": source_url
            }
        else:
            # For multi-year requests where CSV fallback failed, try web scraping for multiple years
            available_years = self._get_available_years()
            if not available_years:
                logger.warning(f"Could not determine available years for {category_type or 'general'} exports data")
                return {"data": [], "source": "no_years_found", "source_url": source_url}
            
            # Fetch data for each available year and combine
            all_data = []
            years_with_data = 0
            
            logger.info(f"Fetching exports data for all {len(available_years)} available years")
            
            # Start with the most recent years, which are more likely to work
            for yr in sorted(available_years, reverse=True):
                try:
                    # Limit to recent years to avoid excessive requests
                    if len(all_data) > 100 and yr < datetime.now().year - 5:
                        logger.info(f"Stopping at year {yr} - already have sufficient data")
                        break
                        
                    year_params = params.copy()
                    year_params['ano'] = str(yr)  # Convert to string for consistency
                    
                    # Try to get data for this year
                    yr_result = self._get_exports_data(year_params, category_type, yr)
                    if yr_result and yr_result.get("data"):
                        all_data.extend(yr_result["data"])
                        years_with_data += 1
                        logger.info(f"Added {len(yr_result['data'])} exports records for year {yr}")
                except Exception as e:
                    logger.error(f"Error fetching exports data for year {yr}: {str(e)}")
            
            logger.info(f"Retrieved exports data for {years_with_data} out of {len(available_years)} years attempted")
            
            # If we got no data from web scraping, try one last CSV fallback
            if not all_data:
                fallback_data = self._fallback_to_csv('exports', category_type, None)
                if fallback_data and fallback_data.get("data"):
                    logger.info(f"Using CSV fallback after all web scraping attempts failed")
                    return fallback_data
            
            return {
                "data": all_data,
                "source": "web_scraping_multi_year",
                "source_url": source_url
            }
            
    def _filter_unwanted_rows(self, records):
        """
        Filter out unwanted header and footer rows from the exports data.
        
        Args:
            records (list): List of record dictionaries
            
        Returns:
            list: Filtered list of records
        """
        if not records:
            return []
            
        # Define patterns for rows to exclude
        exclude_patterns = [
            # Common patterns in navigation rows
            "DOWNLOAD", "TOPO", "VOLTAR", "«", "»", "‹", "›",
            # Header rows that might be duplicated
            "PAÍS", "PAIS", "QUANTIDADE", "VALOR"
        ]
        
        # Common countries that should be KEPT (not filtered out)
        valid_countries = [
            "argentina", "chile", "uruguai", "paraguai", "bolívia", "brasil",
            "alemanha", "portugal", "itália", "italia", "frança", "franca", "espanha",
            "estados unidos", "china", "japão", "japao", "austrália", "australia"
        ]
        
        filtered_records = []
        for record in records:
            # Skip empty records
            if not record or all(not val for val in record.values()):
                continue
                
            # Check if record contains exclude patterns
            should_exclude = False
            
            for pattern in exclude_patterns:
                for value in record.values():
                    if isinstance(value, str) and pattern.lower() in value.lower():
                        # Exception: if this is a country name row, keep it
                        is_country_row = any(country in value.lower() for country in valid_countries)
                        if not is_country_row:
                            should_exclude = True
                            break
                if should_exclude:
                    break
            
            # Skip navigation/control rows
            if should_exclude:
                continue
                
            # Skip header rows (all uppercase)
            all_uppercase = True
            text_values_count = 0
            for key, value in record.items():
                if isinstance(value, str) and len(value) > 1:
                    text_values_count += 1
                    if not value.isupper():
                        all_uppercase = False
                        break
            
            # Only exclude if all text values are uppercase and there are multiple text values
            if all_uppercase and text_values_count > 1:
                continue
                
            # Skip rows with invalid or irrelevant data
            # Skip common footer elements
            if any(footer in str(record).lower() for footer in ["copyright", "embrapa", "loiva", "cnpuv", "banco de dados"]):
                continue
                
            # Clean and normalize the record before keeping it
            clean_record = {}
            for key, value in record.items():
                if isinstance(value, str):
                    if key.lower() in ["quantidade", "quantidade (kg)", "valor", "valor (us$)"]:
                        # Clean numeric values
                        clean_value = value.replace(".", "").replace(",", ".")
                        try:
                            clean_record[key] = float(clean_value) if clean_value and clean_value not in ['-', 'n/a'] else 0.0
                        except ValueError:
                            clean_record[key] = value
                    else:
                        # Normalize country names to title case
                        if key.lower() in ["país", "pais"] and value.lower() in valid_countries:
                            clean_record[key] = value.title()
                        else:
                            clean_record[key] = value
                else:
                    clean_record[key] = value
            
            filtered_records.append(clean_record)
        
        logger.info(f"Filtered {len(records) - len(filtered_records)} unwanted rows from exports data")
        return filtered_records
        
    def _try_excel_source(self, category_type, year):
        """
        Try to get data from official Excel sources for recent years
        
        Args:
            category_type: Category of data
            year: Year to fetch
            
        Returns:
            Dict with data or empty dict on failure
        """
        # This would connect to official source Excel files
        # Implementation depends on whether the files are accessible
        # For now, return empty to fall back to other methods
        return {"data": []}
