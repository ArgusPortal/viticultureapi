from app.scraper.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

class ImportsScraper(BaseScraper):
    def get_imports_data(self, year=None):
        """
        Get imports data for a specific year or for all available years.
        
        Args:
            year: Optional year to filter data
            
        Returns:
            Dict with fetched data
        """
        try:
            params = {
                'opcao': 'opt_05',  # CORRECTED: Imports option is opt_05
                'subopcao': 'subopt_00'  # All imports
            }
            
            return self._get_imports_data(params, None, year)
        except Exception as e:
            logger.error(f"Error in imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_wine_imports(self, year=None):
        """Get table wine imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # CORRECTED: Imports option is opt_05
                'subopcao': 'subopt_01'  # Wine imports
            }
            return self._get_imports_data(params, 'wine', year)
        except Exception as e:
            logger.error(f"Error in wine imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_fresh_imports(self, year=None):
        """Get fresh grape imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # CORRECTED: Imports option is opt_05
                'subopcao': 'subopt_03'  # Fresh grape imports
            }
            return self._get_imports_data(params, 'fresh', year)
        except Exception as e:
            logger.error(f"Error in fresh grape imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_juice_imports(self, year=None):
        """Get juice imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # CORRECTED: Imports option is opt_05
                'subopcao': 'subopt_05'  # Juice imports
            }
            return self._get_imports_data(params, 'juice', year)
        except Exception as e:
            logger.error(f"Error in juice imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_sparkling_imports(self, year=None):
        """Get sparkling wine imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # CORRECTED: Imports option is opt_05
                'subopcao': 'subopt_02'  # Sparkling imports
            }
            return self._get_imports_data(params, 'sparkling', year)
        except Exception as e:
            logger.error(f"Error in sparkling imports scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_raisins_imports(self, year=None):
        """Get raisins imports data for a specific year."""
        try:
            params = {
                'opcao': 'opt_05',  # CORRECTED: Imports option is opt_05
                'subopcao': 'subopt_04'  # Raisins imports
            }
            return self._get_imports_data(params, 'raisins', year)
        except Exception as e:
            logger.error(f"Error in raisins imports scraping: {str(e)}", exc_info=True)
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
        # Same pattern as exports but for imports
        # Create source URL for debugging
        source_url = f"{self.BASE_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        
        # Try CSV fallback first, especially for multi-year queries
        if not year:
            fallback_data = self._fallback_to_csv('imports', category_type, None)
            if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                logger.info(f"Successfully loaded multi-year {category_type or 'general'} imports data from CSV")
                return fallback_data
        
        # If specific year is requested or CSV fallback failed
        if year:
            # Validate year is within acceptable range
            if not (self.MIN_YEAR <= year <= self.MAX_YEAR):
                logger.warning(f"Year {year} is outside valid range ({self.MIN_YEAR}-{self.MAX_YEAR})")
                return {"data": [], "source": "invalid_year", "source_url": source_url}
                
            # Try web scraping for the specific year
            year_params = params.copy()
            year_params['ano'] = year
            
            soup = self._get_soup(self.BASE_URL, year_params)
            if not soup:
                logger.warning(f"Failed to get data for year {year}")
                
                # Try CSV fallback for that year
                fallback_data = self._fallback_to_csv('imports', category_type, year)
                if fallback_data and fallback_data.get("data"):
                    logger.info(f"Successfully loaded {category_type or 'general'} imports data for year {year} from CSV")
                    return fallback_data
                
                return {"data": [], "source": "no_data_found", "source_url": source_url}
            
            # Extract table data
            df = self._extract_table_data(soup)
            
            if df.empty:
                logger.warning(f"No data found for year {year}")
                return {"data": [], "source": "empty_data", "source_url": source_url}
            
            # Process data
            records = df.to_dict('records')
            
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
            
            for yr in available_years:
                try:
                    year_params = params.copy()
                    year_params['ano'] = yr
                    
                    soup = self._get_soup(self.BASE_URL, year_params)
                    if not soup:
                        logger.warning(f"Failed to get imports data for year {yr}")
                        continue
                    
                    df = self._extract_table_data(soup)
                    
                    if df.empty:
                        logger.warning(f"No imports data found for year {yr}")
                        continue
                    
                    records = df.to_dict('records')
                    
                    # Add year to records if not present
                    for record in records:
                        if 'Ano' not in record or not record['Ano']:
                            record['Ano'] = yr
                    
                    all_data.extend(records)
                    years_with_data += 1
                    logger.info(f"Added {len(records)} imports records for year {yr}")
                except Exception as e:
                    logger.error(f"Error fetching imports data for year {yr}: {str(e)}")
            
            logger.info(f"Retrieved imports data for {years_with_data} out of {len(available_years)} years attempted")
            
            return {
                "data": all_data,
                "source": "web_scraping_multi_year",
                "source_url": source_url
            }
