import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class BaseScraper:
    BASE_URL = "http://vitibrasil.cnpuv.embrapa.br/index.php"
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    
    def __init__(self):
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retry_strategy))
    
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
        Extracts table data from the soup.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            pandas.DataFrame: Extracted data
        """
        if soup is None:
            logger.warning("No soup provided to extract table data")
            return pd.DataFrame()
            
        try:
            # Dump the first few tables for debugging
            tables = soup.find_all('table', limit=5)
            logger.info(f"Found {len(tables)} tables in the page")
            
            for i, table in enumerate(tables):
                logger.debug(f"Table {i} structure: {table.prettify()[:300]}...")
            
            # Filter out tables that likely contain author information
            data_tables = []
            for table in tables:
                text = table.get_text().lower()
                # Skip tables that appear to be author info, navigation, or other non-data
                if any(term in text for term in ['loiva maria', 'carlos alberto', 'copyright', 'menu', 'navigation']):
                    logger.info(f"Skipping likely non-data table: {text[:50]}...")
                    continue
                data_tables.append(table)
            
            if not data_tables:
                logger.warning("No data tables found on the page")
                return pd.DataFrame()
            
            # Try to find the best table with actual data
            main_table = None
            max_rows = 0
            
            for table in data_tables:
                rows = table.find_all('tr')
                if len(rows) > max_rows:
                    max_rows = len(rows)
                    main_table = table
            
            if not main_table:
                # If no good candidates, fall back to original method
                for selector in ['table.tabDados', 'table.tabelaDados', 'table.table', 'table']:
                    main_table = soup.select_one(selector)
                    if main_table:
                        # Skip tables with author information
                        if 'loiva maria' in main_table.get_text().lower() or 'carlos alberto' in main_table.get_text().lower():
                            logger.info(f"Skipping author info table found with selector: {selector}")
                            continue
                        logger.info(f"Found table with selector: {selector}")
                        break
            
            if not main_table:
                logger.warning("No suitable data table found on the page")
                return pd.DataFrame()
            
            # Try multiple header detection methods
            headers = []
            
            # Method 1: Look for th elements in the first row
            header_row = main_table.select_one('tr:first-child')
            if header_row:
                th_elements = header_row.find_all('th')
                if th_elements:
                    headers = [th.get_text(strip=True) for th in th_elements]
                    # Check if these are real headers or just formatting
                    if any(len(h) < 1 for h in headers) or any(h.lower() in ['loiva', 'carlos', 'embrapa'] for h in headers):
                        logger.info("First row contains likely non-header th elements, trying other methods")
                        headers = []
            
            # Method 2: Look for th elements with tabTitulo class
            if not headers:
                th_elements = main_table.select('tr.tabTitulo th')
                if th_elements:
                    headers = [th.get_text(strip=True) for th in th_elements]
            
            # Method 3: Look for the first row with td elements that might be headers
            if not headers:
                first_row = main_table.select_one('tr:first-child')
                if first_row:
                    td_elements = first_row.find_all('td')
                    headers_candidate = [td.get_text(strip=True) for td in td_elements]
                    # Make sure these are real headers, not author info or empty cells
                    if all(len(h) > 0 for h in headers_candidate) and not any(name.lower() in ' '.join(headers_candidate).lower() for name in ['loiva', 'carlos', 'embrapa']):
                        headers = headers_candidate
                    else:
                        logger.info("First row td elements don't appear to be real headers")
            
            # Method 4: Look for any elements with bold or strong formatting
            if not headers:
                bold_cells = main_table.select('tr:first-child td b') or main_table.select('tr:first-child td strong')
                if bold_cells:
                    headers = [cell.get_text(strip=True) for cell in bold_cells]
            
            # Method 5: If still no headers, use CSV fallback header names if possible for this data type
            if not headers or len(set(headers)) < len(headers):  # Check for duplicate headers
                # Look for possible headers in the body of the table
                potential_headers = []
                rows = main_table.find_all('tr')
                if len(rows) > 1:  # Skip header row
                    for row in rows[1:3]:  # Check the first couple of data rows
                        cells = row.find_all(['td', 'th'])
                        if cells and len(cells) > 2:  # Only consider rows with enough columns
                            first_cell_text = cells[0].get_text(strip=True)
                            # If first cell looks like a header/category
                            if first_cell_text and not first_cell_text.isdigit() and len(first_cell_text) > 1:
                                potential_headers.append(first_cell_text)
                
                if potential_headers:
                    logger.info(f"Using data row text as column indicators: {potential_headers[:3]}...")
                    # Create generic headers but with counts
                    col_count = max([len(row.find_all(['td', 'th'])) for row in rows])
                    headers = ['Index'] + [f"Column{i+1}" for i in range(col_count-1)]
                else:
                    # Method 6: If all else fails, create generic headers based on max column count
                    col_count = max([len(row.find_all(['td', 'th'])) for row in rows])
                    if col_count > 0:
                        headers = [f"Column{i+1}" for i in range(col_count)]
                        logger.warning(f"Using generic headers: {headers}")
                    
            if not headers:
                logger.warning("Cabeçalhos da tabela não encontrados")
                return pd.DataFrame()
                
            logger.info(f"Found headers: {headers}")
            
            # Ensure header uniqueness
            if len(set(headers)) < len(headers):
                unique_headers = []
                seen = set()
                for header in headers:
                    if header in seen:
                        count = 1
                        while f"{header}_{count}" in seen:
                            count += 1
                        unique_headers.append(f"{header}_{count}")
                        seen.add(f"{header}_{count}")
                    else:
                        unique_headers.append(header)
                        seen.add(header)
                
                logger.warning(f"Fixed duplicate headers. Original: {headers}, New: {unique_headers}")
                headers = unique_headers
                
            # Extract rows - skip the first row if it contains headers
            rows = []
            start_idx = 1 if main_table.select_one('tr:first-child th') or (len(main_table.find_all('tr')) > 0 and len(headers) > 0) else 0
            
            # Make sure we have the right number of headers for the data we'll extract
            row_cells = []
            for row in main_table.find_all('tr')[start_idx:]:
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if cells and len(cells) > 1:  # Skip empty or near-empty rows
                    row_cells.append(cells)
            
            # If we found cells but they have different lengths than the headers, adjust headers
            if row_cells and all(len(cells) != len(headers) for cells in row_cells[:3]):
                max_len = max([len(cells) for cells in row_cells])
                if max_len > 0:
                    logger.warning(f"Adjusting headers from {len(headers)} to {max_len} columns based on data")
                    headers = [f"Column{i+1}" for i in range(max_len)]
            
            # Now process rows for extraction
            for row in main_table.find_all('tr')[start_idx:]:
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if not cells:
                    continue
                
                # Skip rows that appear to be author information or other non-data
                if any('loiva maria' in cell.lower() or 'carlos alberto' in cell.lower() for cell in cells):
                    logger.info(f"Skipping author info row: {cells}")
                    continue
                
                # Fill or trim cells to match header count
                if len(cells) < len(headers):
                    cells = cells + [''] * (len(headers) - len(cells))
                elif len(cells) > len(headers):
                    cells = cells[:len(headers)]
                    
                rows.append(cells)
                    
            if not rows:
                logger.warning("No data rows found in table")
                return pd.DataFrame()
                
            # Create DataFrame
            df = pd.DataFrame(rows, columns=headers)
            logger.info(f"Extracted {len(df)} rows of data")
            
            # Identify and remove rows that don't appear to be data (headers, footers, etc.)
            if len(df) > 2:  # Only clean if we have enough rows
                # Drop rows that are mostly empty
                empty_threshold = 0.7  # Drop if more than 70% of cells are empty
                df = df.dropna(thresh=int(len(df.columns) * (1 - empty_threshold)))
                
                # If there are year columns, make sure values are numeric where expected
                year_cols = [col for col in df.columns if any(year_term in col.lower() for year_term in ['ano', 'year', '20', '19'])]
                if year_cols and len(df) > 0:
                    for col in year_cols:
                        # Try to convert to numeric, coercing errors to NaN
                        pd.to_numeric(df[col], errors='coerce')
                
                logger.info(f"After cleaning: {len(df)} rows of data")
            
            return df
        except Exception as e:
            logger.error(f"Error extracting table data: {str(e)}", exc_info=True)
            return pd.DataFrame()
    
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
