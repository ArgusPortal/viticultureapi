# Detalhamento Técnico: Módulo de Utilitários

Este documento fornece um detalhamento técnico do módulo de utilitários da ViticultureAPI, explicando as funções e classes auxiliares que dão suporte às funcionalidades principais da aplicação.

## 1. Visão Geral (`app/utils/`)

O diretório `utils` contém funções e classes utilitárias que são usadas em diferentes partes da aplicação para tarefas comuns de processamento, limpeza e análise de dados. Estes componentes são projetados para serem reutilizáveis e focados em responsabilidades específicas.

### 1.1. Organização do Módulo

```
app/utils/
├── __init__.py           # Exports das funções e classes principais
├── data_cleaner.py       # Utilitários para limpeza de dados
├── data_analysis.py      # Utilitários para análise de dados
├── converters.py         # Funções de conversão entre formatos
└── validators.py         # Funções de validação simples
```

## 2. Utilitários de Limpeza de Dados (`app/utils/data_cleaner.py`)

Este módulo fornece funções para limpar dados brutos, especialmente aqueles obtidos via scraping web.

### 2.1. clean_navigation_arrows

Função especializada para remover artefatos de setas de navegação em dados raspados:

```python
def clean_navigation_arrows(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove navigation arrow entries from scraped data results and fix data structure.
    
    This function:
    1. Removes navigation arrow entries ("«‹›»")
    2. Fixes duplicate quantity fields by keeping only "Quantidade (L.)" when both are present
    3. Cleans navigation arrows from quantity values before they cause conversion errors
    
    Args:
        data_list: Lista de dicionários com dados a serem limpos
        
    Returns:
        Lista de dicionários com dados limpos
    """
```

Esta função é crucial para o processamento de dados, pois:
1. **Identifica e remove entradas de navegação**: Elimina itens que são puramente de navegação de páginas (como setas).
2. **Resolve campos duplicados**: Corrige a estrutura de dados quando há campos redundantes.
3. **Limpa valores com caracteres especiais**: Remove caracteres que poderiam causar problemas em análises subsequentes.

Processo de limpeza implementado:
- Utiliza expressões regulares para identificar padrões de setas de navegação
- Identifica e remove itens inteiros que correspondem a controles de navegação
- Limpa caracteres problemáticos de campos específicos
- Resolve campos duplicados mantendo a versão mais específica
- Gera logs detalhados sobre o processo de limpeza

### 2.2. safe_float_conversion

Função para converter valores para float de forma segura:

```python
def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float, handling navigation arrows and other invalid formats.
    Returns the default value if conversion fails.
    
    Args:
        value: Valor a ser convertido
        default: Valor padrão caso a conversão falhe
        
    Returns:
        Valor convertido para float ou valor padrão
    """
```

Esta função resolve vários problemas comuns em dados extraídos:
- Conversão segura de diferentes formatos (strings com vírgulas ou pontos como separador decimal)
- Tratamento de valores nulos retornando um padrão configurável
- Remoção automática de caracteres não numéricos antes da conversão
- Logging de tentativas malsucedidas para diagnóstico

## 3. Análise de Dados (`app/utils/data_analysis.py`)

O módulo `data_analysis.py` implementa classes auxiliares para análise de dados vitivinícolas.

### 3.1. WineDataAnalyzer

Classe utilitária para analisar dados de produção vinícola:

```python
class WineDataAnalyzer:
    """
    Utility class for analyzing wine production data from VitiBrasil API.
    """
    
    @staticmethod
    def clean_quantity(quantity_str: str) -> float:
        """
        Convert string quantity to float, handling special characters.
        
        Args:
            quantity_str: String representation of quantity (e.g. "169.762.429")
            
        Returns:
            float: Cleaned quantity value
        """
```

Principais funcionalidades:

#### 3.1.1. Preparação de Dados

```python
@staticmethod
def prepare_dataframe(data: List[Dict]) -> pd.DataFrame:
    """
    Convert API response data to a clean DataFrame.
    
    Args:
        data: List of dictionaries from API response
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with proper types
    """
```

Este método prepara os dados para análise:
- Removendo linhas de cabeçalho/rodapé
- Convertendo quantidades para valores numéricos
- Eliminando entradas inválidas

#### 3.1.2. Análise Comparativa

```python
@staticmethod
def compare_years(data_year1: List[Dict], data_year2: List[Dict], 
                 year1: int, year2: int) -> pd.DataFrame:
    """
    Compare production between two different years.
    """
```

Permite comparar dados entre anos diferentes:
- Alinhando produtos correspondentes
- Calculando variações percentuais
- Identificando tendências de crescimento/queda

#### 3.1.3. Análise de Produtos Principais

```python
@staticmethod
def get_top_products(df: pd.DataFrame, n: int = 10, 
                    exclude_categories: bool = True) -> pd.DataFrame:
    """
    Get top N products by quantity.
    """
```

Identifica os produtos mais relevantes:
- Classificando por volume de produção
- Opção para excluir categorias gerais
- Flexibilidade para definir o número de itens

#### 3.1.4. Verificação de Consistência de APIs

```python
@staticmethod
def compare_endpoints(general_data: List[Dict], wine_data: List[Dict]) -> Dict:
    """
    Compare data from general production endpoint with wine production endpoint
    to determine if they return the same data.
    """
```

Ferramenta para garantir consistência entre endpoints:
- Compara estrutura de dados
- Identifica diferenças em produtos
- Detecta discrepâncias em quantidades

Esta funcionalidade é especialmente útil para:
- Testes de integração
- Verificações de qualidade de dados
- Diagnóstico de problemas em APIs

#### 3.1.5. Relatórios

```python
@staticmethod
def create_endpoint_comparison_report(result: Dict) -> str:
    """
    Create a readable report from endpoint comparison results.
    """
```

Gera relatórios em formato Markdown para facilitar a análise:
- Resumo de consistência
- Detalhes sobre diferenças encontradas
- Formatação clara para revisão humana

## 4. Integração com Sistema de Pipeline

Os utilitários são integrados ao sistema de pipeline através dos transformadores:

```python
# Exemplo de uso em um transformador
from app.utils.data_cleaner import clean_navigation_arrows, safe_float_conversion

class DataCleaningTransformer(Transformer):
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if "data" in data and isinstance(data["data"], list):
            # Aplicar função de limpeza
            data["data"] = clean_navigation_arrows(data["data"])
            
            # Converter valores numéricos
            for item in data["data"]:
                if "Quantidade" in item:
                    item["Quantidade"] = safe_float_conversion(item["Quantidade"])
                    
        return data
```

Esta integração permite:
1. Encapsular lógica de limpeza para reutilização
2. Manter transformadores focados em orquestração de alto nível
3. Aplicar técnicas consistentes de limpeza em diferentes contextos

## 5. Casos de Uso

### 5.1. Processamento de Dados Raspados

```python
# Após obter dados via scraping
raw_data = scraper.extract_table("http://vitibrasil.cnpuv.embrapa.br/")

# Aplicar limpeza
clean_data = clean_navigation_arrows(raw_data)

# Converter para formato adequado
df = WineDataAnalyzer.prepare_dataframe(clean_data)

# Analisar principais produtos
top_products = WineDataAnalyzer.get_top_products(df, n=5)
```

### 5.2. Comparação de Tendências

```python
# Obter dados de dois anos diferentes
data_2021 = api_client.get_production(year=2021)
data_2022 = api_client.get_production(year=2022)

# Comparar anos
comparison = WineDataAnalyzer.compare_years(
    data_2021["data"], 
    data_2022["data"], 
    2021, 
    2022
)

# Filtrar produtos com aumento significativo
growing_products = comparison[comparison["Variação_Percentual"] > 10]
```

### 5.3. Verificação de Consistência de APIs

```python
# Verificar consistência entre endpoints
general_data = api_client.get("/api/v1/production")["data"]
wine_data = api_client.get("/api/v1/production/wine")["data"]

# Comparar resultados
comparison = WineDataAnalyzer.compare_endpoints(general_data, wine_data)

# Gerar relatório
report = WineDataAnalyzer.create_endpoint_comparison_report(comparison)

# Salvar ou exibir relatório
if not comparison["same_data"]:
    with open("endpoint_discrepancies.md", "w") as f:
        f.write(report)
```

## 6. Boas Práticas Implementadas

As funções utilitárias seguem várias boas práticas:

1. **Funções puras**: Minimizam efeitos colaterais, facilitando testes
2. **Logging detalhado**: Registram informações úteis para diagnóstico
3. **Tratamento robusto de erros**: Lidam graciosamente com formatos inesperados
4. **Tipagem estática**: Utilizam type hints para melhorar IDE support
5. **Documentação completa**: Docstrings detalhados explicando propósito e uso
6. **Métodos estáticos**: Facilitam uso sem necessidade de instanciação

## 7. Conclusão

O módulo de utilitários da ViticultureAPI fornece componentes essenciais para o processamento confiável de dados em toda a aplicação. As funções de limpeza e análise encapsulam lógicas reutilizáveis que garantem consistência e qualidade dos dados processados.

A clara separação entre utilitários de baixo nível e transformadores de alto nível permite manter o código organizado e facilitar a manutenção. Esta abordagem modular também facilita a extensão do sistema com novas funcionalidades de processamento de dados.
