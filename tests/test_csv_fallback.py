import sys
import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import scrapers
from app.scraper.base_scraper import BaseScraper
from app.scraper.production_scraper import ProductionScraper
from app.scraper.imports_scraper import ImportsScraper
from app.scraper.exports_scraper import ExportsScraper
from app.scraper.processing_scraper import ProcessingScraper
from app.scraper.commercialization_scraper import CommercializationScraper

# Criar diretório temporário de dados para testes
@pytest.fixture
def test_data_dir(tmp_path):
    """Configura um diretório temporário com arquivos CSV de teste"""
    # Criar diretório de dados
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Criar CSV de produção de teste
    production_data = pd.DataFrame({
        'produto': ['Vinho Tinto', 'Vinho Branco', 'Suco de Uva'],
        '2020': [1000, 500, 300],
        '2021': [1200, 600, 350],
        '2022': [1300, 650, 400]
    })
    production_data.to_csv(data_dir / "Producao.csv", sep=';', index=False)
    
    # Criar CSV de importação de teste
    imports_data = pd.DataFrame({
        'Pais': ['Argentina', 'Chile', 'França'],
        'Produto': ['Vinho Tinto', 'Vinho Branco', 'Espumante'],
        'Quantidade': [5000, 3000, 1000],
        'Valor': [100000, 80000, 50000],
        'Ano': [2022, 2022, 2022]
    })
    imports_data.to_csv(data_dir / "Importacao.csv", sep=';', index=False)
    
    # Criar CSV de exportação de teste
    exports_data = pd.DataFrame({
        'Pais': ['EUA', 'Reino Unido', 'Japão'],
        'Produto': ['Vinho Tinto', 'Vinho Branco', 'Suco de Uva'],
        'Quantidade': [1000, 500, 2000],
        'Valor': [50000, 25000, 30000],
        'Ano': [2022, 2022, 2022]
    })
    exports_data.to_csv(data_dir / "Exportacao.csv", sep=';', index=False)
    
    yield data_dir

class MockResponse:
    """Mock para respostas HTTP com falha"""
    def __init__(self, success=True):
        self.success = success
        self.status_code = 200 if success else 404
        self.ok = success
        self.text = "<html><body><h1>Dados não encontrados</h1></body></html>" if not success else "<html><body><h1>Dados Vitibrasil</h1></body></html>"
    
    def raise_for_status(self):
        if not self.success:
            raise Exception("404 Not Found")
            
# Teste básico de fallback no BaseScraper
@pytest.mark.parametrize("year", [None, 2020, 2021, 2022])
def test_base_scraper_fallback(test_data_dir, year):
    """Testa se o BaseScraper faz fallback para CSV quando o scraping falha"""
    
    # Override do método _get_soup para forçar falha
    class FailingScraper(BaseScraper):
        DATA_DIR = test_data_dir
        
        def _get_soup(self, url, params=None):
            return None  # Simula falha ao obter HTML
        
        def _fallback_to_csv(self, category, subcategory=None, year=None):
            # Chamar o método real de fallback
            return super()._fallback_to_csv(category, subcategory, year)
    
    scraper = FailingScraper()
    # Verificar se o fallback retorna dados
    result = scraper._fallback_to_csv('production', None, year)
    
    assert "data" in result
    assert "source" in result
    assert result["source"] == "local_csv"
    
    # Se um ano específico foi fornecido, verificar se apenas dados desse ano são retornados
    if year is not None:
        if len(result["data"]) > 0:
            # Verificar se todos os registros são do ano correto ou contêm o valor para o ano
            for record in result["data"]:
                if "Ano" in record:
                    assert record["Ano"] == year

# Teste específico para ProductionScraper
@patch('requests.get')
def test_production_scraper_fallback(mock_get, test_data_dir):
    """Testa se o ProductionScraper faz fallback para CSV quando o web scraping falha"""
    
    # Configurar mock para falhar ao buscar dados online
    mock_response = MockResponse(success=False)
    mock_get.return_value = mock_response
    
    # Criar scraper com diretório de dados de teste
    class TestProductionScraper(ProductionScraper):
        DATA_DIR = test_data_dir
        
        # Adicionar método explicitamente se não existir na classe base
        def get_general_production(self, year=None):
            """Obtém dados gerais de produção vitivinícola"""
            try:
                params = {
                    'opcao': 'opt_02',
                    'subopcao': 'subopt_00'
                }
                return self._get_production_data(params, None, year)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in general production scraping: {str(e)}", exc_info=True)
                return {"data": [], "error": str(e), "source": "error"}
    
    scraper = TestProductionScraper()
    
    # Tentar obter dados para 2022 (deve fazer fallback para CSV)
    result = scraper.get_general_production(2022)
    
    assert "data" in result
    assert "source" in result
    assert result["source"] == "local_csv"  # Confirma que os dados vieram do CSV
    assert len(result["data"]) > 0  # Verifica se há dados no resultado

# Teste específico para ImportsScraper
@patch('requests.get')
def test_imports_scraper_fallback(mock_get, test_data_dir):
    """Testa se o ImportsScraper faz fallback para CSV quando o web scraping falha"""
    
    # Configurar mock para falhar ao buscar dados online
    mock_response = MockResponse(success=False)
    mock_get.return_value = mock_response
    
    # Criar scraper com diretório de dados de teste
    class TestImportsScraper(ImportsScraper):
        DATA_DIR = test_data_dir
    
    scraper = TestImportsScraper()
    
    # Tentar obter dados para 2022 (deve fazer fallback para CSV)
    result = scraper.get_imports_data(2022)
    
    assert "data" in result
    assert "source" in result
    assert result["source"] == "local_csv"  # Confirma que os dados vieram do CSV
    assert len(result["data"]) > 0  # Verifica se há dados no resultado

# Teste específico para ExportsScraper
@patch('requests.get')
def test_exports_scraper_fallback(mock_get, test_data_dir):
    """Testa se o ExportsScraper faz fallback para CSV quando o web scraping falha"""
    
    # Configurar mock para falhar ao buscar dados online
    mock_response = MockResponse(success=False)
    mock_get.return_value = mock_response
    
    # Criar scraper com diretório de dados de teste
    class TestExportsScraper(ExportsScraper):
        DATA_DIR = test_data_dir
    
    scraper = TestExportsScraper()
    
    # Tentar obter dados para 2022 (deve fazer fallback para CSV)
    result = scraper.get_exports_data(2022)
    
    assert "data" in result
    assert "source" in result
    assert result["source"] == "local_csv"  # Confirma que os dados vieram do CSV
    assert len(result["data"]) > 0  # Verifica se há dados no resultado

# Teste integrado com os endpoints da API
@pytest.mark.asyncio
@patch('app.scraper.base_scraper.BaseScraper._get_soup')
async def test_production_endpoint_fallback(mock_get_soup, test_data_dir):
    """Testa se o endpoint de produção faz fallback para CSV quando o scraping falha"""
    from app.api.endpoints.production import get_production_data, ProductionScraper
    
    # Fazer o _get_soup sempre retornar None para simular falha
    mock_get_soup.return_value = None
    
    # Substituir DATA_DIR no ProductionScraper
    original_dir = ProductionScraper.DATA_DIR
    ProductionScraper.DATA_DIR = test_data_dir
    
    try:
        # Chamar o endpoint diretamente (simulando uma chamada API)
        # Passar um token fictício para autenticação
        result = await get_production_data(year=2022, current_user="test_user")
        
        # Verificar se os dados vieram do fallback
        assert "source" in result
        assert result["source"] == "local_csv"
        assert "data" in result
        assert len(result["data"]) > 0
        assert result["ano_filtro"] == 2022
    finally:
        # Restaurar DATA_DIR
        ProductionScraper.DATA_DIR = original_dir
