from app.scraper.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

class ProcessingScraper(BaseScraper):
    def get_processing_data(self, year=None):
        """
        Retrieve general processing data from VitiBrasil.
        
        Args:
            year (int, optional): Year to filter data. Defaults to None.
            
        Returns:
            dict: Processing data
        """
        try:
            params = {
                'opcao': 'opt_03',
            }
            
            # If a specific year is requested, validate it's in the acceptable range
            if year is not None:
                if not (self.MIN_YEAR <= year <= self.MAX_YEAR):
                    logger.warning(f"Year {year} is outside valid range ({self.MIN_YEAR}-{self.MAX_YEAR})")
                    return {"data": [], "source": "invalid_year"}
                    
                params['ano'] = year
                
                # Try to get data for the specific year
                soup = self._get_soup(self.BASE_URL, params)
                if not soup:
                    logger.warning(f"Failed to get data for year {year}")
                    # Try CSV fallback for that year
                    fallback_data = self._fallback_to_csv('processing', None, year)
                    if fallback_data and fallback_data.get("data"):
                        logger.info(f"Successfully loaded processing data for year {year} from CSV")
                        return fallback_data
                    
                    return {"data": [], "source": "no_data_found"}
                
                # Extract table data
                df = self._extract_table_data(soup)
                
                if df.empty:
                    logger.warning(f"No data found for year {year}")
                    return {"data": [], "source": "empty_data"}
                
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
                    "source_url": f"{self.BASE_URL}?opcao=opt_03&ano={year}"
                }
            else:
                # Try CSV fallback first for multi-year data
                fallback_data = self._fallback_to_csv('processing', None, None)
                if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                    logger.info(f"Successfully loaded multi-year processing data from CSV")
                    return fallback_data
                
                # For multi-year requests, try to get available years
                available_years = self._get_available_years()
                if not available_years:
                    logger.warning("Could not determine available years for processing data")
                    return {"data": [], "source": "no_years_found"}
                
                # Fetch data for each available year and combine
                all_data = []
                years_with_data = 0
                
                logger.info(f"Fetching processing data for all {len(available_years)} available years")
                
                for yr in available_years:
                    try:
                        # Fix: use consistent variable naming and ensure proper type
                        year_params = params.copy()
                        year_params['ano'] = str(yr)  # Convert to string to ensure compatibility
                        
                        soup = self._get_soup(self.BASE_URL, year_params)
                        if not soup:
                            logger.warning(f"Failed to get processing data for year {yr}")
                            continue
                        
                        df = self._extract_table_data(soup)
                        
                        if df.empty:
                            logger.warning(f"No processing data found for year {yr}")
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
                        logger.info(f"Added {len(records)} processing records for year {yr}")
                    except Exception as e:
                        logger.error(f"Error fetching processing data for year {yr}: {str(e)}")
                
                logger.info(f"Retrieved processing data for {years_with_data} out of {len(available_years)} years attempted")
                
                return {
                    "data": all_data,
                    "source": "web_scraping_multi_year",
                    "source_url": f"{self.BASE_URL}?opcao=opt_03"
                }
        except Exception as e:
            logger.error(f"Error in processing scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def get_vinifera_processing(self, year=None):
        """Get vinifera grape processing data."""
        try:
            params = {
                'opcao': 'opt_03',
                'subopcao': 'subopt_01'  # Vinifera processing - UPDATED to match correct URL
            }
            return self._get_processing_data_by_category(params, 'vinifera', year)
        except Exception as e:
            logger.error(f"Error in vinifera processing scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
            
    def get_american_processing(self, year=None):
        """Get American and hybrid grape processing data."""
        try:
            params = {
                'opcao': 'opt_03',
                'subopcao': 'subopt_02'  # American processing - UPDATED to match correct URL
            }
            return self._get_processing_data_by_category(params, 'american', year)
        except Exception as e:
            logger.error(f"Error in American processing scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
            
    def get_table_processing(self, year=None):
        """Get table grape processing data."""
        try:
            params = {
                'opcao': 'opt_03',
                'subopcao': 'subopt_03'  # Table processing - UPDATED to match correct URL
            }
            return self._get_processing_data_by_category(params, 'table', year)
        except Exception as e:
            logger.error(f"Error in table processing scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
            
    def get_unclassified_processing(self, year=None):
        """Get unclassified grape processing data."""
        try:
            params = {
                'opcao': 'opt_03',
                'subopcao': 'subopt_04'  # Unclassified processing - This was already correct
            }
            return self._get_processing_data_by_category(params, 'unclassified', year)
        except Exception as e:
            logger.error(f"Error in unclassified processing scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
    
    def _get_processing_data_by_category(self, params, category, year=None):
        """Helper method to get processing data by category."""
        try:
            # If a specific year is requested, validate it's in the acceptable range
            if year is not None:
                if not (self.MIN_YEAR <= year <= self.MAX_YEAR):
                    logger.warning(f"Year {year} is outside valid range ({self.MIN_YEAR}-{self.MAX_YEAR})")
                    return {"data": [], "source": "invalid_year"}
                    
                params['ano'] = year
                
                # Try to get data for the specific year
                soup = self._get_soup(self.BASE_URL, params)
                if not soup:
                    logger.warning(f"Failed to get {category} processing data for year {year}")
                    # Try CSV fallback for that year
                    fallback_data = self._fallback_to_csv('processing', category, year)
                    if fallback_data and fallback_data.get("data"):
                        logger.info(f"Successfully loaded {category} processing data for year {year} from CSV")
                        return fallback_data
                    
                    return {"data": [], "source": "no_data_found"}
                
                # Extract table data
                df = self._extract_table_data(soup)
                
                if df.empty:
                    logger.warning(f"No {category} processing data found for year {year}")
                    return {"data": [], "source": "empty_data"}
                
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
                    "source_url": f"{self.BASE_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
                }
            else:
                # Try CSV fallback first for multi-year data
                fallback_data = self._fallback_to_csv('processing', category, None)
                if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                    logger.info(f"Successfully loaded multi-year {category} processing data from CSV")
                    return fallback_data
                
                # For multi-year requests, try to get available years
                available_years = self._get_available_years()
                if not available_years:
                    logger.warning(f"Could not determine available years for {category} processing data")
                    return {"data": [], "source": "no_years_found"}
                
                # Fetch data for each available year and combine
                all_data = []
                years_with_data = 0
                
                logger.info(f"Fetching {category} processing data for all {len(available_years)} available years")
                
                for yr in available_years:
                    try:
                        # Fix: use consistent variable naming and ensure proper type
                        year_params = params.copy()
                        year_params['ano'] = str(yr)  # Convert to string to ensure compatibility
                        
                        soup = self._get_soup(self.BASE_URL, year_params)
                        if not soup:
                            logger.warning(f"Failed to get {category} processing data for year {yr}")
                            continue
                        
                        df = self._extract_table_data(soup)
                        
                        if df.empty:
                            logger.warning(f"No {category} processing data found for year {yr}")
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
                        logger.info(f"Added {len(records)} {category} processing records for year {yr}")
                    except Exception as e:
                        logger.error(f"Error fetching {category} processing data for year {yr}: {str(e)}")
                
                logger.info(f"Retrieved {category} processing data for {years_with_data} out of {len(available_years)} years attempted")
                
                return {
                    "data": all_data,
                    "source": "web_scraping_multi_year",
                    "source_url": f"{self.BASE_URL}?{'&'.join([f'{k}={v}' for k, v in params.items() if k != 'ano'])}"
                }
        except Exception as e:
            logger.error(f"Error in {category} processing scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}

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
        
        logger.info(f"Filtered {len(records) - len(filtered_records)} unwanted header/footer rows from processing data")
        return filtered_records
