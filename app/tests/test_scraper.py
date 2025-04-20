import pytest
from app.scraper.production_scraper import ProductionScraper
import pandas as pd

@pytest.fixture
def scraper():
    return ProductionScraper()

def test_wine_production_scraper(scraper):
    result = scraper.get_wine_production()
    assert result, "O resultado não deve estar vazio"
    
    # Converter para DataFrame para facilitar a verificação
    if not isinstance(result, pd.DataFrame):
        df = pd.DataFrame(result)
    else:
        df = result
        
    # Verificar se temos dados
    assert not df.empty, "O DataFrame não deve estar vazio"
    
    # Verificar colunas esperadas (se houver dados)
    if not df.empty:
        assert "Produto" in df.columns, "A coluna 'Produto' deve existir"
        assert "Quantidade" in df.columns, "A coluna 'Quantidade' deve existir"
        
        # Verificar tipos de dados se a coluna existir e tiver valores
        if "Quantidade" in df.columns and not df["Quantidade"].empty:
            # Tentar converter para numérico para verificar se é possível
            try:
                pd.to_numeric(df["Quantidade"])
                assert True, "A coluna 'Quantidade' pode ser convertida para numérico"
            except:
                assert False, "A coluna 'Quantidade' deve ser numérica"
