import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import Counter

logger = logging.getLogger(__name__)

class BaseScraper:
    BASE_URL = "http://vitibrasil.cnpuv.embrapa.br/index.php"
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    
    # Constants for year range (used by all scrapers)
    MIN_YEAR = 1970
    MAX_YEAR = 2023
    
    def __init__(self):
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retry_strategy))
    
    def _safe_find_all(self, element, *args, **kwargs):
        """Safely call find_all with error handling"""
        try:
            if element is None:
                return []
            return element.find_all(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in find_all: {str(e)}")
            return []
    
    def _get_fallback_years(self):
        """Return a fixed range of years based on the known data range (1970-2023)"""
        fallback_years = list(range(self.MIN_YEAR, self.MAX_YEAR + 1))
        logger.info(f"Using complete year range from {self.MIN_YEAR} to {self.MAX_YEAR}")
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
                        if self.MIN_YEAR <= year <= self.MAX_YEAR:
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
                    option_elements = self._safe_find_all(soup, 'option')
                    if option_elements:
                        for option in option_elements:
                            year_text = option.text.strip() if hasattr(option, 'text') else ""
                            if year_text.isdigit():
                                try:
                                    year = int(year_text)
                                    # Ensure year is within valid range
                                    if self.MIN_YEAR <= year <= self.MAX_YEAR:
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
    
    def _get_soup(self, url, params=None):
        """
        Makes a request to the URL and returns a BeautifulSoup object.
        
        Args:
            url (str): URL to request
            params (dict, optional): Parameters for the request
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        try:
            logger.info(f"Making request to {url} with params {params}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Log the first 500 characters of the response for debugging
            logger.debug(f"Response preview: {response.text[:500]}...")
            
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error making request: {str(e)}")
            return None
    
    def _extract_table_data(self, soup):
        """
        Improved table data extraction with better error handling and validation.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            pandas.DataFrame: Extracted data
        """
        if soup is None:
            logger.warning("No soup provided to extract table data")
            return pd.DataFrame()
            
        try:
            # Find all tables
            tables = self._safe_find_all(soup, 'table')
            logger.info(f"Found {len(tables)} tables in the page")
            
            if not tables:
                logger.warning("No tables found in the page")
                return pd.DataFrame()
                
            # Select the best table using a scoring approach
            best_table, best_score = None, -1
            
            for idx, table in enumerate(tables):
                # Skip tiny tables (likely navigation)
                rows = self._safe_find_all(table, 'tr')
                if len(rows) < 3:
                    continue
                    
                # Calculate a score for how likely this is to be a data table
                score = self._calculate_table_score(table)
                logger.debug(f"Table {idx}: score={score}, rows={len(rows)}")
                
                if score > best_score:
                    best_score = score
                    best_table = table
            
            if not best_table:
                logger.warning("No suitable data table found on the page")
                return pd.DataFrame()
                
            # Extract headers using multiple strategies
            headers = self._extract_table_headers(best_table)
            
            if not headers:
                logger.warning("Could not determine table headers")
                return pd.DataFrame()
                
            # Make headers unique
            headers = self._ensure_unique_headers(headers)
            logger.info(f"Using headers: {headers}")
            
            # Extract data rows with validation
            rows_data = self._extract_table_rows(best_table, headers)
            
            if not rows_data:
                logger.warning("No data rows found in table")
                return pd.DataFrame()
                
            # Create DataFrame and clean numeric columns
            df = pd.DataFrame(rows_data, columns=headers)
            df = self._clean_numeric_columns(df)
            
            logger.info(f"Extracted {len(df)} rows of data")
            return df
        except Exception as e:
            logger.error(f"Error extracting table data: {str(e)}", exc_info=True)
            return pd.DataFrame()

    def _calculate_table_score(self, table):
        """Calculate a score for how likely a table is to contain data"""
        score = 0
        
        # Tables with more rows are likely data tables
        rows = self._safe_find_all(table, 'tr')
        score += len(rows) * 2
        
        # Tables with th elements are likely data tables
        ths = self._safe_find_all(table, 'th')
        score += len(ths) * 3
        
        # Tables with numeric values are likely data tables
        text = table.get_text()
        
        # Check for patterns that look like numbers with thousand separators
        if re.search(r'\d{1,3}(\.\d{3})+', text):
            score += 10
            
        # Tables with country names or product names are likely data tables
        text_lower = text.lower()
        if any(country in text_lower for country in ['brasil', 'argentina', 'chile', 'uruguai']):
            score += 5
        if any(product in text_lower for product in ['vinho', 'uva', 'suco', 'espumante']):
            score += 5
            
        return score

    def _extract_table_headers(self, table):
        """Extract headers from table using multiple strategies"""
        # Strategy 1: Find th elements
        th_elements = self._safe_find_all(table, 'th')
        if th_elements:
            headers = [th.get_text(strip=True) for th in th_elements]
            if all(len(h) > 0 for h in headers):
                return headers
        
        # Strategy 2: Use first row
        first_row = table.find('tr')
        if first_row:
            cells = self._safe_find_all(first_row, ['td', 'th'])
            headers = [cell.get_text(strip=True) for cell in cells]
            if all(len(h) > 0 for h in headers):
                return headers
        
        # Strategy 3: Look for rows with header-like content
        for row in self._safe_find_all(table, 'tr')[:3]:  # Check first 3 rows
            cells = self._safe_find_all(row, ['td', 'th'])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Check if this row has header-like content
            if any(keyword in ' '.join(cell_texts).lower() for keyword in 
                  ['país', 'pais', 'produto', 'quantidade', 'valor']):
                return cell_texts
        
        # Strategy 4: Infer headers from table structure
        rows = self._safe_find_all(table, 'tr')
        if rows:
            # Find most common cell count
            cell_counts = [len(self._safe_find_all(row, ['td', 'th'])) for row in rows]
            if cell_counts:
                most_common = Counter(cell_counts).most_common(1)[0][0]
                
                # Default import/export headers
                if most_common >= 3:
                    return ['País', 'Quantidade (Kg)', 'Valor (US$)'][:most_common]
                else:
                    return [f"Column{i+1}" for i in range(most_common)]
        
        return []

    def _ensure_unique_headers(self, headers):
        """Make sure headers are unique by appending numbers if needed"""
        if len(set(headers)) == len(headers):
            return headers
            
        unique_headers = []
        seen = set()
        
        for header in headers:
            if header in seen:
                i = 1
                while f"{header}_{i}" in seen:
                    i += 1
                unique_headers.append(f"{header}_{i}")
                seen.add(f"{header}_{i}")
            else:
                unique_headers.append(header)
                seen.add(header)
        
        return unique_headers

    def _extract_table_rows(self, table, headers):
        """Extract table rows with validation and filtering"""
        rows_data = []
        header_row_found = False
        
        for row in self._safe_find_all(table, 'tr'):
            cells = self._safe_find_all(row, ['td', 'th'])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Skip rows that match headers (to avoid duplicate headers)
            if set(cell_texts) == set(headers):
                header_row_found = True
                continue
                
            # Skip empty rows
            if not cell_texts or all(not text for text in cell_texts):
                continue
                
            # Skip navigation/control rows
            if any(text in ['TOPO', 'DOWNLOAD', '«', '»', '‹', '›'] for text in cell_texts):
                continue
                
            # Skip footer/copyright rows
            if any('copyright' in text.lower() for text in cell_texts):
                continue
            if any('embrapa' in text.lower() for text in cell_texts):
                continue
                
            # Make sure row has the right number of cells
            if len(cell_texts) < len(headers):
                # Pad with empty strings
                cell_texts = cell_texts + [''] * (len(headers) - len(cell_texts))
            elif len(cell_texts) > len(headers):
                # Truncate
                cell_texts = cell_texts[:len(headers)]
                
            rows_data.append(cell_texts)
        
        return rows_data

    def _clean_numeric_columns(self, df):
        """Clean numeric columns in the dataframe"""
        for col in df.columns:
            if any(term in col.lower() for term in ['quantidade', 'valor', 'kg', 'us$']):
                try:
                    # First replace thousand separators (dots)
                    df[col] = df[col].astype(str).str.replace('.', '')
                    # Then replace decimal separators (commas)
                    df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
                except Exception as e:
                    logger.warning(f"Could not convert column {col} to numeric: {str(e)}")
        
        return df
    
    def _fallback_to_csv(self, category, subcategory=None, year=None):
        """
        Fallback to load data from local CSV files when web scraping fails.
        
        Args:
            category (str): Data category (e.g., 'production', 'processing')
            subcategory (str, optional): Data subcategory
            year (int, optional): Year to filter data
            
        Returns:
            pandas.DataFrame or dict: Loaded data
        """
        try:
            # Map API categories to CSV filenames
            filename_mapping = {
                'production': {
                    None: 'Producao.csv',
                    'wine': 'Producao.csv',  # Filter for wine data
                    'grape': 'Producao.csv',  # Filter for grape data
                    'derivative': 'Producao.csv',  # Filter for derivative data
                },
                'processing': {
                    None: 'Processa.csv',
                    'american': 'ProcessaAmericanas.csv',
                    'table': 'ProcessaMesa.csv',
                    'unclassified': 'ProcessaSemclass.csv',
                    'vinifera': 'ProcessaViniferas.csv',
                },
                'commercialization': {
                    None: 'Comercio.csv',
                },
                'imports': {
                    None: 'Imp.csv',
                    'sparkling': 'ImpEspumantes.csv',
                    'fresh': 'ImpFrescas.csv',
                    'raisins': 'ImpPassas.csv',
                    'juice': 'ImpSuco.csv',
                    'wine': 'ImpVinhos.csv',
                },
                'exports': {
                    None: 'Exp.csv',
                    'sparkling': 'ExpEspumantes.csv',
                    'juice': 'ExpSuco.csv',
                    'grape': 'ExpUva.csv',
                    'wine': 'ExpVinho.csv',
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