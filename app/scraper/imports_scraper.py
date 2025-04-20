import requests
from bs4 import BeautifulSoup
from app.scraper.base_scraper import BaseScraper
import pandas as pd
import logging
import os
import re
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

class ImportsScraper(BaseScraper):
    """Scraper for import data from VitiBrasil."""
    
    def get_imports_data(self, year=None):
        """
        Get combined imports data from all subcategories for a specific year or all years.
        
        Args:
            year: Optional year to filter data
            
        Returns:
            Dict with fetched data
        """
        try:
            # First, try CSV fallback which is most reliable for aggregate data
            fallback_data = self._fallback_to_csv('imports', None, year)
            if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                logger.info(f"Using CSV fallback for all imports data")
                return fallback_data
            
            # Get data from individual subcategories
            combined_data = []
            sources = set()
            
            # Define subcategories to fetch with their category identifiers
            subcategory_methods = [
                {'method': self.get_wine_imports, 'category': 'vinhos'},
                {'method': self.get_sparkling_imports, 'category': 'espumantes'},
                {'method': self.get_fresh_imports, 'category': 'uvas-frescas'},
                {'method': self.get_raisins_imports, 'category': 'passas'},
                {'method': self.get_juice_imports, 'category': 'suco'}
            ]
            
            # Fetch and combine data from all subcategories
            for subcat in subcategory_methods:
                try:
                    subcategory_data = subcat['method'](year)
                    if subcategory_data and "data" in subcategory_data and subcategory_data["data"]:
                        # Add category identifier to each record
                        for record in subcategory_data["data"]:
                            record['categoria'] = subcat['category']
                            
                        combined_data.extend(subcategory_data["data"])
                        if "source" in subcategory_data:
                            sources.add(subcategory_data["source"])
                        logger.info(f"Added {len(subcategory_data['data'])} records from {subcat['category']}")
                except Exception as e:
                    logger.error(f"Error fetching data from {subcat['category']}: {str(e)}")
            
            # Return combined data
            if combined_data:
                return {
                    "data": combined_data,
                    "source": "+".join(sources) if sources else "combined_imports",
                    "source_url": f"{self.BASE_URL}?opcao=opt_05"
                }
            
            # If we couldn't get any data, return empty result
            logger.warning("No import data could be retrieved from any subcategory")
            return {"data": [], "source": "no_data_found", "source_url": f"{self.BASE_URL}?opcao=opt_05"}
        except Exception as e:
            logger.error(f"Error in imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_wine_imports(self, year=None):
        """Get table wine imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # Imports option is opt_05
                'subopcao': 'subopt_01'  # Wine imports
            }
            return self._get_imports_data_safely(params, 'wine', year)
        except Exception as e:
            logger.error(f"Error in wine imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_sparkling_imports(self, year=None):
        """Get sparkling wine imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # Imports option is opt_05
                'subopcao': 'subopt_02'  # Sparkling imports
            }
            return self._get_imports_data_safely(params, 'sparkling', year)
        except Exception as e:
            logger.error(f"Error in sparkling imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_fresh_imports(self, year=None):
        """
        Get fresh grape imports data for a specific year or all available years.
        
        Args:
            year (int, optional): Specific year to get data for
            
        Returns:
            dict: Data, source information, and optional error message
        """
        try:
            # Define the parameters for fresh grape imports
            params = {
                'opcao': 'opt_05',  # Imports option
                'subopcao': 'subopt_03'  # Fresh grape imports
            }
            
            # Call the generic method with the specific parameters
            return self._get_imports_data_safely(params, 'fresh', year)
        except Exception as e:
            logger.error(f"Error in fresh grape imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_raisins_imports(self, year=None):
        """Get raisins imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # Imports option is opt_05
                'subopcao': 'subopt_04'  # Raisins imports
            }
            return self._get_imports_data_safely(params, 'raisins', year)
        except Exception as e:
            logger.error(f"Error in raisins imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_juice_imports(self, year=None):
        """Get juice imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # Imports option is opt_05
                'subopcao': 'subopt_05'  # Juice imports
            }
            return self._get_imports_data_safely(params, 'juice', year)
        except Exception as e:
            logger.error(f"Error in juice imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def _get_imports_data(self, params, category_type=None, year=None):
        """
        Generic method to fetch imports data.
        
        Args:
            params: Request parameters
            category_type: Optional category filter
            year: Optional year filter
            
        Returns:
            Dict with fetched data
        """
        # Create source URL for debugging
        source_url = self._build_source_url(params, year)
        
        # Try CSV fallback first, especially for multi-year queries
        if not year:
            fallback_data = self._fallback_to_csv('imports', category_type, None)
            if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                logger.info(f"Successfully loaded multi-year {category_type or 'general'} imports data from CSV")
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
                    return self._get_imports_data(new_params, category_type, current_year)
                return {"data": [], "source": "invalid_year", "source_url": source_url}
                
            # Try web scraping for the specific year
            year_params = params.copy()
            year_params['ano'] = str(year)  # Convert to string for consistency
            
            soup = self._get_soup(self.BASE_URL, year_params)
            if not soup:
                logger.warning(f"Failed to get data for year {year}")
                
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
                    fallback_data = self._fallback_to_csv('imports', category_type, year)
                    if fallback_data and fallback_data.get("data"):
                        logger.info(f"Successfully loaded {category_type or 'general'} imports data for year {year} from CSV")
                        return fallback_data
                    
                    # If all else fails, try the official VitiBrasil Excel files for recent years
                    if year >= 2015:
                        logger.info(f"Trying Excel data sources for year {year}")
                        excel_data = self._try_excel_source(category_type, year)
                        if excel_data and excel_data.get("data"):
                            return excel_data
                    
                    return {"data": [], "source": "no_data_found", "source_url": source_url}
            
            # Extract table data with our improved method
            df = self._extract_table_data(soup)
            
            if df.empty:
                logger.warning(f"No data found for year {year}")
                
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
                    fallback_data = self._fallback_to_csv('imports', category_type, year)
                    if fallback_data and fallback_data.get("data"):
                        logger.info(f"Successfully loaded {category_type or 'general'} imports data for year {year} from CSV after web extraction failed")
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
                logger.warning(f"Could not determine available years for {category_type or 'general'} imports data")
                return {"data": [], "source": "no_years_found", "source_url": source_url}
            
            # Fetch data for each available year and combine
            all_data = []
            years_with_data = 0
            
            logger.info(f"Fetching imports data for all {len(available_years)} available years")
            
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
                    yr_result = self._get_imports_data(year_params, category_type, yr)
                    if yr_result and yr_result.get("data"):
                        all_data.extend(yr_result["data"])
                        years_with_data += 1
                        logger.info(f"Added {len(yr_result['data'])} imports records for year {yr}")
                except Exception as e:
                    logger.error(f"Error fetching imports data for year {yr}: {str(e)}")
            
            logger.info(f"Retrieved imports data for {years_with_data} out of {len(available_years)} years attempted")
            
            # If we got no data from web scraping, try one last CSV fallback
            if not all_data:
                fallback_data = self._fallback_to_csv('imports', category_type, None)
                if fallback_data and fallback_data.get("data"):
                    logger.info(f"Using CSV fallback after all web scraping attempts failed")
                    return fallback_data
            
            return {
                "data": all_data,
                "source": "web_scraping_multi_year",
                "source_url": source_url
            }
            
    def _get_imports_data_safely(self, params, category_type, year=None):
        """
        Wrapper around _get_imports_data with improved error handling and validation.
        
        Args:
            params: Request parameters
            category_type: Category to fetch
            year: Optional year filter
            
        Returns:
            dict: Data and source information
        """
        # First, try the CSV fallback if no specific year is requested (more reliable)
        if not year:
            fallback_data = self._fallback_to_csv('imports', category_type, None)
            if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                logger.info(f"Using CSV data for {category_type or 'general'} imports")
                return fallback_data
        
        # Then try web scraping 
        try:
            result = self._get_imports_data(params, category_type, year)
            
            # Validate the result - make sure we have data
            if result and "data" in result and len(result["data"]) > 0:
                logger.info(f"Successfully retrieved {len(result['data'])} records for {category_type}")
                return result
            
            # If no data from web scraping, always try CSV fallback
            logger.warning(f"Web scraping returned no data for {category_type}, trying CSV fallback")
            fallback_data = self._fallback_to_csv('imports', category_type, year)
            if fallback_data and fallback_data.get("data"):
                return fallback_data
                
            # If still no data, return empty result with clear source info
            return {"data": [], "source": "no_data_found", 
                    "source_url": self._build_source_url(params, year)}
        except Exception as e:
            logger.error(f"Error retrieving {category_type} import data: {str(e)}", exc_info=True)
            
            # On error, try CSV fallback
            fallback_data = self._fallback_to_csv('imports', category_type, year)
            if fallback_data and fallback_data.get("data"):
                return fallback_data
                
            return {"data": [], "error": str(e), "source": "error"}
    
    def _filter_unwanted_rows(self, records):
        """
        Filter out unwanted header and footer rows from the imports data.
        
        Args:
            records (list): List of record dictionaries
            
        Returns:
            list: Filtered list of records with cleaned values
        """
        if not records:
            return []
            
        # Define patterns for rows to exclude
        exclude_patterns = [
            "DOWNLOAD", "TOPO", "VOLTAR", "«", "»", "‹", "›"
        ]
        
        # Common countries that should be KEPT
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
                
            # Check for exclude patterns but protect country names
            should_exclude = False
            for pattern in exclude_patterns:
                pattern_found = False
                for value in record.values():
                    if not isinstance(value, str):
                        continue
                    
                    # Check if value contains exclude pattern
                    if pattern.lower() in value.lower():
                        # Don't exclude if this is a valid country name
                        is_country = any(country in value.lower() for country in valid_countries)
                        if not is_country:
                            pattern_found = True
                            break
                
                if pattern_found:
                    should_exclude = True
                    break
                    
            if should_exclude:
                continue
                
            # Clean and normalize the record
            clean_record = {}
            
            for key, value in record.items():
                if isinstance(value, str):
                    # Clean numeric values
                    if any(term in key.lower() for term in ["quantidade", "valor"]):
                        clean_value = value.replace(".", "").replace(",", ".")
                        try:
                            clean_record[key] = float(clean_value) if clean_value and clean_value != '-' else 0.0
                        except ValueError:
                            clean_record[key] = value
                    # Normalize country names
                    elif key.lower() in ["país", "pais"] and any(country in value.lower() for country in valid_countries):
                        clean_record[key] = value.title()
                    else:
                        clean_record[key] = value
                else:
                    clean_record[key] = value
                    
            filtered_records.append(clean_record)
            
        logger.info(f"Filtered {len(records) - len(filtered_records)} unwanted rows, keeping {len(filtered_records)} records")
        return filtered_records
    
    def _build_source_url(self, params, year=None):
        """Build source URL with proper parameter encoding for debugging"""
        base_params = params.copy()
        if year:
            base_params['ano'] = str(year)
        return f"{self.BASE_URL}?{'&'.join([f'{k}={v}' for k, v in base_params.items()])}"
        
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
