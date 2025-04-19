from app.scraper.base_scraper import BaseScraper
import logging

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
                'opcao': 'opt_06',  # CORRECTED: Exports option is opt_06
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
                'opcao': 'opt_06',  # CORRECTED: Exports option is opt_06
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
                'opcao': 'opt_06',  # CORRECTED: Exports option is opt_06
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
                'opcao': 'opt_06',  # CORRECTED: Exports option is opt_06
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
                'opcao': 'opt_06',  # CORRECTED: Exports option is opt_06
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
            if not (self.MIN_YEAR <= year <= self.MAX_YEAR):
                logger.warning(f"Year {year} is outside valid range ({self.MIN_YEAR}-{self.MAX_YEAR})")
                return {"data": [], "source": "invalid_year", "source_url": source_url}
                
            # Try web scraping for the specific year
            year_params = params.copy()
            year_params['ano'] = str(year)  # Convert to string for consistency
            
            soup = self._get_soup(self.BASE_URL, year_params)
            if not soup:
                logger.warning(f"Failed to get data for year {year}")
                
                # Try CSV fallback for that year
                fallback_data = self._fallback_to_csv('exports', category_type, year)
                if fallback_data and fallback_data.get("data"):
                    logger.info(f"Successfully loaded {category_type or 'general'} exports data for year {year} from CSV")
                    return fallback_data
                
                return {"data": [], "source": "no_data_found", "source_url": source_url}
            
            # Extract table data
            df = self._extract_table_data(soup)
            
            if df.empty:
                logger.warning(f"No data found for year {year}")
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
            
            for yr in available_years:
                try:
                    year_params = params.copy()
                    year_params['ano'] = str(yr)  # Convert to string for consistency
                    
                    soup = self._get_soup(self.BASE_URL, year_params)
                    if not soup:
                        logger.warning(f"Failed to get exports data for year {yr}")
                        continue
                    
                    df = self._extract_table_data(soup)
                    
                    if df.empty:
                        logger.warning(f"No exports data found for year {yr}")
                        continue
                    
                    records = df.to_dict('records')
                    
                    # Filter out unwanted header and footer rows
                    records = self._filter_unwanted_rows(records)
                    
                    # Add year to records if not present
                    for record in records:
                        if 'Ano' not in record or not record['Ano']:
                            record['Ano'] = yr
                    
                    all_data.extend(records)
                    years_with_data += 1
                    logger.info(f"Added {len(records)} exports records for year {yr}")
                except Exception as e:
                    logger.error(f"Error fetching exports data for year {yr}: {str(e)}")
            
            logger.info(f"Retrieved exports data for {years_with_data} out of {len(available_years)} years attempted")
            
            return {
                "data": all_data,
                "source": "web_scraping_multi_year",
                "source_url": source_url
            }
            
    def _filter_unwanted_rows(self, records):
        """
        Filter out unwanted header and footer rows from the processing data.
        
        Args:
            records (list): List of record dictionaries
            
        Returns:
            list: Filtered list of records
        """
        if not records:
            return []
            
        # Define patterns for rows to exclude
        exclude_patterns = [
            # Headers
            {"Sem definição": "ViníferasAmericanas e híbridasUvas de mesaSem classificação"},
            {"Sem definição": "Sem definição", "Quantidade (Kg)": "Quantidade (Kg)"},
            # Footers
            {"Sem definição": "DOWNLOAD"},
            {"Quantidade (Kg)": "TOPO"}
        ]
        
        filtered_records = []
        for record in records:
            # Check if record matches any exclude pattern
            should_exclude = False
            
            for pattern in exclude_patterns:
                matches = True
                for key, value in pattern.items():
                    if key not in record or record[key] != value:
                        matches = False
                        break
                
                if matches:
                    should_exclude = True
                    break
            
            # Also exclude by checking specific values
            if record.get("Sem definição") in ["DOWNLOAD", "TOPO"] or record.get("Quantidade (Kg)") in ["TOPO", "«‹›»"]:
                should_exclude = True
            
            # Only include if it's not in the exclude list
            if not should_exclude:
                filtered_records.append(record)
        
        logger.info(f"Filtered {len(records) - len(filtered_records)} unwanted header/footer rows from exports data")
        return filtered_records
