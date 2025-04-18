import pytest
from app.scraper.production_scraper import ProductionScraper

@pytest.fixture
def scraper():
    return ProductionScraper()

def test_wine_production_scraper(scraper):
    df = scraper.get_wine_production()
    assert not df.empty, "O DataFrame não deve estar vazio"
    
    # Verificar colunas esperadas
    assert "Produto" in df.columns, "A coluna 'Produto' deve existir"
    assert "Quantidade" in df.columns, "A coluna 'Quantidade' deve existir"
    
    # Verificar tipos de dados
    assert df["Quantidade"].dtype == float, "A coluna 'Quantidade' deve ser numérica"
