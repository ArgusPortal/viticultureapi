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
            tables = soup.find_all('table', limit=3)
            for i, table in enumerate(tables):
                logger.debug(f"Table {i} structure: {table.prettify()[:300]}...")
            
            # Try multiple table selectors
            table = None
            for selector in ['table.tabDados', 'table.tabelaDados', 'table.table', 'table']:
                table = soup.select_one(selector)
                if table:
                    logger.info(f"Found table with selector: {selector}")
                    break
                    
            if not table:
                logger.warning("Tabela não encontrada na página")
                return pd.DataFrame()
                
            # Try multiple header detection methods
            headers = []
            
            # Method 1: Look for th elements in the first row
            header_row = table.select_one('tr:first-child')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
                
            # Method 2: Look for th elements with tabTitulo class
            if not headers:
                headers = [th.get_text(strip=True) for th in table.select('tr.tabTitulo th')]
            
            # Method 3: Look for the first row with td elements that might be headers
            if not headers:
                first_row = table.select_one('tr:first-child')
                if first_row:
                    headers = [td.get_text(strip=True) for td in first_row.find_all('td')]
            
            # Method 4: Look for any elements with bold or strong formatting
            if not headers:
                bold_cells = table.select('tr:first-child td b') or table.select('tr:first-child td strong')
                if bold_cells:
                    headers = [cell.get_text(strip=True) for cell in bold_cells]
            
            # Method 5: If still no headers, create generic ones based on column count
            if not headers:
                sample_row = table.select_one('tr')
                if sample_row:
                    col_count = len(sample_row.find_all(['td', 'th']))
                    if col_count > 0:
                        headers = [f"Column{i+1}" for i in range(col_count)]
                        logger.warning(f"Using generic headers: {headers}")
                    
            if not headers:
                logger.warning("Cabeçalhos da tabela não encontrados")
                return pd.DataFrame()
                
            logger.info(f"Found headers: {headers}")
                
            # Extract rows - skip the first row if it contains headers
            rows = []
            start_idx = 1 if table.select_one('tr:first-child th') else 0
            
            for row in table.find_all('tr')[start_idx:]:
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if cells and len(cells) == len(headers):
                    rows.append(cells)
                elif cells:
                    logger.warning(f"Row has {len(cells)} cells, expected {len(headers)}. Row data: {cells}")
                    
            if not rows:
                logger.warning("No data rows found in table")
                return pd.DataFrame()
                
            # Create DataFrame
            df = pd.DataFrame(rows, columns=headers)
            logger.info(f"Extracted {len(df)} rows of data")
            
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
