from .base_scraper import BaseScraper
import pandas as pd

class ProductionScraper(BaseScraper):
    def get_wine_production(self, year=None):
        """Obtém dados de produção de vinhos"""
        params = {
            'opcao': 'opt_02',
            'subopcao': 'subopt_03'
        }
        
        if year:
            params['ano'] = year
            
        soup = self._get_soup(self.BASE_URL, params)
        df = self._extract_table_data(soup)
        
        # Limpar e converter dados
        if not df.empty and 'Quantidade' in df.columns:
            df['Quantidade'] = df['Quantidade'].str.replace('.', '')
            df['Quantidade'] = df['Quantidade'].str.replace(',', '.').astype(float)
            
        return df
        
    def get_grape_production(self, year=None):
        """Obtém dados de produção de uvas"""
        params = {
            'opcao': 'opt_02',
            'subopcao': 'subopt_01'
        }
        
        if year:
            params['ano'] = year
            
        soup = self._get_soup(self.BASE_URL, params)
        return self._extract_table_data(soup)
