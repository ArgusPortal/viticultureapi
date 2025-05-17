# Detalhamento Técnico: Estrutura de Dados

Este documento detalha a organização e utilização da pasta `data` na ViticultureAPI, explicando como os dados são armazenados, processados e utilizados pelo sistema como mecanismo de fallback.

## 1. Estrutura da Pasta `data`

A pasta `data` é organizada hierarquicamente para refletir diferentes estágios do processamento de dados e categorias de informação:

```
data/
├── raw/              # Dados brutos extraídos via scraping
│   ├── production/   # Dados de produção por ano
│   ├── exports/      # Dados de exportação por ano 
│   ├── imports/      # Dados de importação por ano
│   └── processing/   # Dados de processamento por ano
│
├── processed/        # Dados após limpeza e transformação
│   ├── production/
│   ├── exports/
│   └── imports/
│
├── backup/           # Snapshots históricos para recuperação
│
└── examples/         # Dados de exemplo para documentação e testes
```

## 2. Mecanismo de Fallback para Scraping

Um dos elementos mais importantes da pasta `data` é seu papel como sistema de fallback quando o scraping web falha:

### 2.1. Processo de Fallback

Quando ocorre uma falha na extração de dados via web scraping, o sistema segue este fluxo:

1. Tenta extrair dados do site VitiBrasil usando os scrapers correspondentes
2. Se falhar (site indisponível, mudança na estrutura HTML, etc.), busca CSV local em `data/raw/[categoria]/[ano].csv`
3. Registra o uso de fallback nos logs para monitoramento

```python
# Trecho simplificado da implementação de fallback nos scrapers
def get_data(self, year):
    try:
        # Tenta obter dados via scraping
        data = self._scrape_web_data(year)
        return data
    except ScrapingException:
        # Se falhar, busca dados de CSV local
        logger.warning(f"Scraping failed for {year}, using CSV fallback")
        return self._get_from_csv(year)
```

### 2.2. Implementação no FileRepository

A classe `CSVFileRepository` gerencia o acesso aos arquivos CSV de fallback:

```python
class CSVFileRepository(FileRepository):
    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = base_dir
        
    async def get_data(self, category: str, year: Optional[int] = None) -> Dict[str, Any]:
        filepath = self._build_filepath(category, year)
        
        if not os.path.exists(filepath):
            return {"error": f"No data file found for {category}, year {year}"}
        
        try:
            df = pd.read_csv(filepath)
            return {
                "data": df.to_dict("records"),
                "source": "csv_fallback",
                "source_file": filepath
            }
        except Exception as e:
            logger.error(f"Error reading CSV file {filepath}: {str(e)}")
            return {"error": str(e)}
```

## 3. Categorias de Dados

### 3.1. Dados de Produção (`data/raw/production/`)

Contém informações sobre produção de uvas, vinhos e derivados no Brasil:

- **Formato**: CSV com colunas específicas para cada subcategoria
- **Nomenclatura de arquivos**: `[ano].csv` para dados gerais, `wine_[ano].csv` para dados específicos de vinhos
- **Estrutura típica**: 
  - Região
  - Tipo de produto
  - Quantidade (litros/toneladas)
  - Valor (quando disponível)

### 3.2. Dados de Importação (`data/raw/imports/`)

Detalha a importação de produtos vitivinícolas por país de origem:

- **Subcategorias**: vinhos, espumantes, uvas frescas, passas, sucos
- **Colunas chave**: país de origem, quantidade, valor em dólares
- **Séries históricas**: arquivos separados por ano desde aproximadamente 2000

### 3.3. Dados de Exportação (`data/raw/exports/`)

Similar à importação, mas focado em produtos brasileiros exportados:

- **Granularidade**: por país de destino e por categoria de produto
- **Métricas**: volume, valor, preço médio

### 3.4. Dados de Processamento (`data/raw/processing/`)

Informações sobre processamento industrial de diferentes tipos de uva:

- **Categorização**: viníferas, americanas, híbridas, mesa
- **Informações regionais**: dados por estado produtor
- **Aplicações**: processamento para vinhos, sucos, outros derivados

## 4. Dados Processados

A pasta `data/processed/` armazena dados após passarem por:

1. **Limpeza**: remoção de artefatos de scraping (como setas de navegação)
2. **Normalização**: padronização de formatos de valores
3. **Enriquecimento**: cálculos adicionais, métricas derivadas
4. **Validação**: dados validados conforme regras de negócio

Estes dados processados são usados para:
- Análises mais avançadas
- Geração de relatórios
- Respostas de API que exigem dados pré-agregados

## 5. Estratégia de Atualização

Os dados seguem uma estratégia de atualização mista:

### 5.1. Atualização Automática

- Um job periódico realiza scraping para atualizar CSVs
- Prioridade para dados mais recentes (ano atual e anterior)
- Registros de tentativas em logs para auditoria

### 5.2. Atualização Manual

- Script `data_updater.py` para forçar atualização específica
- Interface administrativa (planejada) para gerenciar dados
- Opção para carregar dados de outras fontes confiáveis

## 6. Integração com o Pipeline

Os arquivos em `data/` são integrados ao sistema de pipeline:

```python
# Exemplo de uso em um pipeline
pipeline = Pipeline()
pipeline.add_extractor(CSVExtractor("data/raw/production/2022.csv"))
pipeline.add_transformer(DataCleaningTransformer())
pipeline.add_loader(DataFrameToCSVLoader("data/processed/production/2022_cleaned.csv"))
resultado = pipeline.execute()
```

Esta integração permite:
1. Processamento em lote de dados históricos
2. Validação e limpeza consistente
3. Geração programática de dados derivados

## 7. Garantia de Qualidade de Dados

Para manter a integridade dos dados armazenados:

### 7.1. Relatórios de Validação

- Armazenados em `data/validation_reports/`
- Gerados automaticamente após atualização de dados
- Métricas de qualidade (completude, consistência, precisão)

### 7.2. Metadados

Cada categoria principal possui um arquivo de metadados com:
- Descrição de colunas e tipos esperados
- Intervalos de valores válidos
- Datas de última atualização
- Fonte original dos dados
- Linhagem de processamento

Este sistema de dados bem estruturado proporciona à API uma grande resistência a falhas externas, garantindo disponibilidade contínua mesmo quando as fontes de dados primárias estão inacessíveis.
