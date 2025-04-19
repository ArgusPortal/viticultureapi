import requests
from bs4 import BeautifulSoup
from app.scraper.base_scraper import BaseScraper
import logging
import os

logger = logging.getLogger(__name__)

class CommercializationScraper(BaseScraper):
    def get_commercialization_data(self, year=None):
        """
        Retrieve commercialization data from VitiBrasil.
        
        Args:
            year (int, optional): Year to filter data. Defaults to None.
            
        Returns:
            dict: Commercialization data
        """
        try:
            params = {
                'opcao': 'opt_04',
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
                    fallback_data = self._fallback_to_csv('commercialization', None, year)
                    if fallback_data and fallback_data.get("data"):
                        logger.info(f"Successfully loaded commercialization data for year {year} from CSV")
                        return fallback_data
                    
                    return {"data": [], "source": "no_data_found"}
                
                # Extract table data
                df = self._extract_table_data(soup)
                
                if df.empty:
                    logger.warning(f"No data found for year {year}")
                    return {"data": [], "source": "empty_data"}
                
                # Process data
                records = df.to_dict('records')
                
                # Add year to records if not present
                for record in records:
                    if 'Ano' not in record or not record['Ano']:
                        record['Ano'] = year
                
                return {
                    "data": records,
                    "source": "web_scraping",
                    "source_url": f"{self.BASE_URL}?opcao=opt_04&ano={year}"
                }
            else:
                # Try CSV fallback first for multi-year data
                fallback_data = self._fallback_to_csv('commercialization', None, None)
                if fallback_data and fallback_data.get("data") and len(fallback_data.get("data", [])) > 0:
                    logger.info(f"Successfully loaded multi-year commercialization data from CSV")
                    return fallback_data
                
                # For multi-year requests, try to get available years
                available_years = self._get_available_years()
                if not available_years:
                    logger.warning("Could not determine available years for commercialization data")
                    return {"data": [], "source": "no_years_found"}
                
                # Fetch data for each available year and combine
                all_data = []
                years_with_data = 0
                
                logger.info(f"Fetching commercialization data for all {len(available_years)} available years")
                
                for yr in available_years:
                    try:
                        # Fix: use consistent variable naming and ensure proper type
                        year_params = params.copy()
                        year_params['ano'] = str(yr)  # Convert to string to ensure compatibility
                        
                        soup = self._get_soup(self.BASE_URL, year_params)
                        if not soup:
                            logger.warning(f"Failed to get commercialization data for year {yr}")
                            continue
                        
                        df = self._extract_table_data(soup)
                        
                        if df.empty:
                            logger.warning(f"No commercialization data found for year {yr}")
                            continue
                        
                        records = df.to_dict('records')
                        
                        # Add year to records if not present
                        for record in records:
                            if 'Ano' not in record or not record['Ano']:
                                record['Ano'] = yr
                        
                        all_data.extend(records)
                        years_with_data += 1
                        logger.info(f"Added {len(records)} commercialization records for year {yr}")
                    except Exception as e:
                        logger.error(f"Error fetching commercialization data for year {yr}: {str(e)}")
                
                logger.info(f"Retrieved commercialization data for {years_with_data} out of {len(available_years)} years attempted")
                
                return {
                    "data": all_data,
                    "source": "web_scraping_multi_year",
                    "source_url": f"{self.BASE_URL}?opcao=opt_04"
                }
        except Exception as e:
            logger.error(f"Error in commercialization scraping: {str(e)}", exc_info=True)
            return {"data": [], "error": str(e), "source": "error"}
