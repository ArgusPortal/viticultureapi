# Detalhamento Técnico: Transformadores de Dados

Este documento fornece um detalhamento técnico da camada de transformação de dados da ViticultureAPI, explicando as classes específicas para processamento de dados de vitivinicultura.

## 1. Visão Geral (`app/transform/`)

O módulo `transform` implementa transformadores especializados para processar diferentes tipos de dados relacionados à vitivinicultura. Estes transformadores são responsáveis por limpar, normalizar e estruturar os dados brutos coletados pelas camadas de repositório.

### 1.1. Organização do Módulo

```
app/transform/
├── __init__.py           # Exports dos transformadores principais
├── viticulture.py        # Transformadores específicos para dados de vitivinicultura
├── generic.py            # Transformadores genéricos reutilizáveis
└── pipelines/            # Pipelines pré-configurados para transformação
    ├── __init__.py
    └── data_processing.py
```

## 2. Transformadores de Vitivinicultura (`app/transform/viticulture.py`)

Este arquivo contém implementações especializadas para transformar diferentes categorias de dados relacionados à vitivinicultura.

### 2.1. ProductionDataTransformer

Transformador que processa dados de produção de vinhos e derivados:

```python
class ProductionDataTransformer(DataFrameTransformer):
    """
    Transformador para dados de produção de vinhos e derivados.
    """
    
    def __init__(self, ano_filtro: Optional[int] = None):
        """
        Inicializa o transformador.
        
        Args:
            ano_filtro: Ano para filtro (opcional)
        """
        super().__init__("production_transformer")
        self.ano_filtro = ano_filtro
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        # Verificar colunas esperadas
        # Limpar nomes das colunas
        # Converter tipos de dados
        # Filtrar por ano
        # Ordenar resultados
        # Eliminar duplicatas
        # Remover dados inválidos
        # ...
```

Este transformador implementa as seguintes operações:
- **Normalização de colunas**: Padroniza nomes de colunas para formato consistente
- **Conversão de tipos**: Garante que dados numéricos sejam do tipo correto
- **Filtragem por ano**: Possibilita filtrar o conjunto de dados por ano específico
- **Ordenação**: Organiza os dados em uma ordem lógica
- **Remoção de duplicatas**: Elimina registros duplicados
- **Limpeza de dados inválidos**: Remove linhas com valores nulos em campos críticos

### 2.2. ImportExportTransformer

Transformador especializado para dados de importação e exportação:

```python
class ImportExportTransformer(DataFrameTransformer):
    """
    Transformador para dados de importação e exportação.
    """
    
    def __init__(self, ano_filtro: Optional[int] = None, pais_filtro: Optional[str] = None):
        """
        Inicializa o transformador.
        
        Args:
            ano_filtro: Ano para filtro (opcional)
            pais_filtro: País para filtro (opcional)
        """
        super().__init__("import_export_transformer")
        self.ano_filtro = ano_filtro
        self.pais_filtro = pais_filtro
```

Características chave:
- Suporta filtro por país (adicional ao filtro por ano)
- Lida com formatos monetários, convertendo strings para valores numéricos
- Realiza limpeza avançada de nomes de países para garantir consistência
- Ordena dados por múltiplos critérios (ano, país, produto)

### 2.3. ProcessingTransformer

Especializado em transformar dados sobre processamento industrial de uvas:

```python
class ProcessingTransformer(DataFrameTransformer):
    """
    Transformador para dados de processamento de uvas.
    """
    
    def __init__(self, ano_filtro: Optional[int] = None):
        """
        Inicializa o transformador.
        
        Args:
            ano_filtro: Ano para filtro (opcional)
        """
        super().__init__("processing_transformer")
        self.ano_filtro = ano_filtro
```

Este transformador lida com:
- Dados de quantidade em quilogramas (diferente das outras categorias que usam litros)
- Categorização de tipos de uva (viníferas, americanas, híbridas)
- Agrupamento de dados por grupo varietal

### 2.4. CommercializationTransformer

Processa dados de comercialização no mercado interno:

```python
class CommercializationTransformer(DataFrameTransformer):
    """
    Transformador para dados de comercialização no mercado interno.
    """
    
    def __init__(self, ano_filtro: Optional[int] = None):
        """
        Inicializa o transformador.
        
        Args:
            ano_filtro: Ano para filtro (opcional)
        """
        super().__init__("commercialization_transformer")
        self.ano_filtro = ano_filtro
```

### 2.5. DataFrameToDictTransformer

Converter DataFrames processados para o formato de dicionário usado nas respostas da API:

```python
class DataFrameToDictTransformer(Transformer[pd.DataFrame, Dict[str, Any]]):
    """
    Transforma um DataFrame em um dicionário estruturado para API.
    """
    
    def __init__(
        self,
        source: str = "pipeline", 
        ano_filtro: Optional[int] = None,
        pais_filtro: Optional[str] = None,
        include_source_url: bool = True,
        source_url: Optional[str] = None
    ):
        """
        Inicializa o transformador.
        
        Args:
            source: Fonte dos dados (scraping, csv, etc.)
            ano_filtro: Ano filtrado (opcional)
            pais_filtro: País filtrado (opcional)
            include_source_url: Se deve incluir URL da fonte
            source_url: URL da fonte dos dados (opcional)
        """
```

Este transformador é crucial para:
- Criar estrutura de resposta padronizada para a API
- Incluir metadados importantes como timestamp, fonte, e informações de filtragem
- Garantir consistência em todas as respostas da API

## 3. Implementação de DataFrameTransformer

Todos os transformadores específicos herdam de uma classe base `DataFrameTransformer` que fornece funcionalidades comuns:

```python
class DataFrameTransformer(Transformer[pd.DataFrame, pd.DataFrame]):
    """Classe base para transformações em DataFrames."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"transformer.{name}")
    
    def drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove linhas duplicadas do DataFrame."""
        original_rows = len(df)
        df = df.drop_duplicates()
        new_rows = len(df)
        
        if original_rows > new_rows:
            self.logger.info(f"Removed {original_rows - new_rows} duplicate rows")
            
        return df
    
    def rename_columns(self, df: pd.DataFrame, rename_map: Dict[str, str]) -> pd.DataFrame:
        """Renomeia colunas com base em um dicionário de mapeamento."""
        return df.rename(columns=rename_map)
```

## 4. Integração com Pipeline

Os transformadores são projetados para serem utilizados no sistema de pipeline da aplicação:

```python
# Exemplo de uso em um pipeline
from app.core.pipeline import Pipeline
from app.repositories import CSVRepository
from app.transform.viticulture import ProductionDataTransformer, DataFrameToDictTransformer

# Criar pipeline
pipeline = Pipeline(name="production_processing")

# Adicionar componentes
pipeline.add_extractor(CSVRepository().read_csv("data/raw/production/2022.csv"))
pipeline.add_transformer(ProductionDataTransformer(ano_filtro=2022))
pipeline.add_transformer(DataFrameToDictTransformer(source="csv", ano_filtro=2022))

# Executar pipeline
result = pipeline.execute()
```

Esta integração permite:
1. Encadeamento de múltiplas transformações
2. Processamento consistente de diferentes tipos de dados
3. Rastreabilidade do fluxo de processamento
4. Reutilização de transformadores em diferentes contextos

## 5. Boas Práticas Implementadas

Os transformadores seguem várias boas práticas:

1. **Imutabilidade**: Não modificam o DataFrame original, retornando novas cópias
2. **Logging detalhado**: Registram informações sobre as transformações realizadas
3. **Tratamento de erros**: Verificam colunas necessárias e lidam com formatos inesperados
4. **Tipagem estática**: Utilizam type hints para melhor IDE support e documentação
5. **Single Responsibility**: Cada transformador tem uma responsabilidade específica
6. **Configuração flexível**: Aceitam parâmetros para personalizar o comportamento

## 6. Conclusão

O sistema de transformação da ViticultureAPI implementa um conjunto coeso de transformadores especializados para diferentes tipos de dados de vitivinicultura. A abordagem baseada em composição permite criar pipelines flexíveis que podem ser adaptados para diferentes necessidades de processamento de dados.

Os transformadores garantem que os dados brutos coletados de diferentes fontes sejam convertidos para um formato consistente e limpo antes de serem disponibilizados pela API, assegurando alta qualidade dos dados e facilitando sua análise e visualização pelos consumidores da API.
