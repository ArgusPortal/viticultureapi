# VitiBrasil API - Documentação Técnica

## 1. Visão Geral

A VitiBrasil API é um projeto desenvolvido para facilitar o acesso programático aos dados de vitivinicultura fornecidos pela Embrapa. O sistema atua como uma camada intermediária que extrai, processa e disponibiliza dados através de endpoints RESTful, permitindo que pesquisadores, empresas e desenvolvedores possam consumir informações sobre produção, processamento, comercialização, importação e exportação de produtos vitivinícolas brasileiros.

## 2. Arquitetura do Sistema

O projeto segue uma arquitetura modular baseada em FastAPI, com componentes especializados para scraping, processamento de dados e disponibilização via API.

```mermaid
graph TD
    Client[Cliente API] --> API[FastAPI Endpoints]
    API --> Scraper[Sistema de Scraping]
    Scraper --> WebSource[VitiBrasil Website]
    Scraper --> CSV[Arquivos CSV de Backup]
    API --> DataAnalysis[Utilitários de Análise]
    
    subgraph Scrapers
        BaseScraper[Base Scraper] --> ProductionScraper[Production Scraper]
        BaseScraper --> ImportsScraper[Imports Scraper]
        BaseScraper --> ExportsScraper[Exports Scraper]
        BaseScraper --> ProcessingScraper[Processing Scraper]
        BaseScraper --> CommercializationScraper[Commercialization Scraper]
    end
    
    subgraph Endpoints
        APIRouter[API Router] --> ProductionAPI[Endpoints de Produção]
        APIRouter --> ImportsAPI[Endpoints de Importação]
        APIRouter --> ExportsAPI[Endpoints de Exportação]
        APIRouter --> ProcessingAPI[Endpoints de Processamento]
        APIRouter --> CommercializationAPI[Endpoints de Comercialização]
    end
    
    Scraper --> Scrapers
    API --> Endpoints
```

### Fluxo de Dados

```mermaid
sequenceDiagram
    participant Cliente
    participant API
    participant Scraper
    participant WebSite
    participant CSV

    Cliente->>API: Requisição de dados
    API->>Scraper: Solicita dados
    Scraper->>WebSite: Tenta obter dados via web scraping
    alt Scraping bem-sucedido
        WebSite->>Scraper: Retorna dados HTML
        Scraper->>Scraper: Extrai e processa dados
    else Scraping falhou
        Scraper->>CSV: Tenta obter dados de backup
        CSV->>Scraper: Retorna dados CSV
    end
    Scraper->>API: Retorna dados formatados
    API->>Cliente: Responde com JSON estruturado
```

## 3. Requisitos Técnicos

### 3.1 Dependências

```
# API Framework
fastapi>=0.95.0
uvicorn>=0.21.1

# Data processing
pandas>=1.5.3
numpy>=1.24.2

# Web scraping
requests>=2.28.2
beautifulsoup4>=4.12.0

# Configuration
python-dotenv>=1.0.0
```

### 3.2 Estrutura de Diretórios

```
viticultureapi/
│
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── commercialization.py
│   │   │   ├── exports.py
│   │   │   ├── imports.py
│   │   │   ├── processing.py
│   │   │   └── production.py
│   │   ├── api.py
│   │   └── __init__.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   ├── production.py
│   │   └── __init__.py
│   │
│   ├── scraper/
│   │   ├── base_scraper.py
│   │   ├── commercialization_scraper.py
│   │   ├── exports_scraper.py
│   │   ├── imports_scraper.py
│   │   ├── processing_scraper.py
│   │   ├── production_scraper.py
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   └── data_analysis.py
│   │
│   ├── tests/
│   │   └── test_scraper.py
│   │
│   ├── main.py
│   └── __init__.py
│
├── data/            # Diretório para arquivos CSV de backup
├── .env             # Variáveis de ambiente
├── requirements.txt # Dependências do projeto
└── README.md        # Documentação básica
```

## 4. Componentes Principais

### 4.1 BaseScraper

A classe `BaseScraper` serve como fundação para todos os scrapers específicos, fornecendo funcionalidades comuns:

- Configuração de sessão HTTP com retry
- Extração de tabelas HTML
- Identificação de anos disponíveis
- Fallback para arquivos CSV locais quando o scraping falha
- Limpeza e formatação de dados numéricos

### 4.2 Scrapers Especializados

- **ProductionScraper**: Extrai dados de produção vitivinícola
- **ImportsScraper**: Extrai dados de importação
- **ExportsScraper**: Extrai dados de exportação
- **ProcessingScraper**: Extrai dados de processamento
- **CommercializationScraper**: Extrai dados de comercialização interna

### 4.3 API Endpoints

Os endpoints da API são organizados em routers específicos para cada categoria de dados:

- `/api/v1/production/`: Dados de produção
- `/api/v1/imports/`: Dados de importação
- `/api/v1/exports/`: Dados de exportação
- `/api/v1/processing/`: Dados de processamento
- `/api/v1/commercialization/`: Dados de comercialização

Todos os endpoints aceitam filtros por ano e retornam respostas padronizadas em formato JSON.

## 5. Desafios e Soluções

### 5.1 Inconsistência nos Dados de Origem

**Desafio**: O site VitiBrasil apresenta inconsistências na estrutura HTML, formatação de tabelas e disponibilidade de dados para diferentes anos.

**Solução**: 
- Implementação de múltiplas estratégias de extração de tabelas
- Sistema de pontuação para selecionar a melhor tabela em cada página
- Validação robusta dos dados extraídos
- Normalização de cabeçalhos e valores numéricos

### 5.2 Falhas no Web Scraping

**Desafio**: O scraping frequentemente falha devido a alterações no site, tempos limite ou problemas na estrutura da página.

**Solução**:
- Sistema de fallback para arquivos CSV locais
- Mecanismo de retry com backoff exponencial
- Logging detalhado para diagnóstico
- Manipulação de exceções em múltiplos níveis

### 5.3 Coleta de Dados para Múltiplos Anos

**Desafio**: Obter dados históricos para todos os anos disponíveis requer múltiplas requisições e pode ser lento.

**Solução**:
- Detecção automática de anos disponíveis
- Estratégia de coleta eficiente para múltiplos anos
- Cache de resultados em arquivos CSV locais

### 5.4 Problema com Dados de Importação

**Desafio**: A opção 'subopt_00' para importações não retornava dados reais, apenas registros vazios com zeros para todos os anos.

**Solução**:
- Implementação de um método que combina dados de todas as subcategorias quando solicitados dados gerais de importação
- Tentativa primária de uso do CSV de fallback para dados agregados
- Combinação de dados de subendpoints funcionais (vinhos, espumantes, uvas frescas, passas, sucos)
- Rastreamento apropriado de fontes para atribuição de origem dos dados

## 6. Como Usar a API

### 6.1 Executando Localmente

```
# Clonar o repositório
git clone https://github.com/argusportal/viticultureapi.git
cd viticultureapi

# Instalar dependências
pip install -r requirements.txt

# Executar o servidor
uvicorn app.main:app --reload
```

### 6.2 Exemplos de Requisições

#### Produção de Vinhos para um Ano Específico
```
GET /api/v1/production/wine?year=2022
```

#### Todos os Dados de Importação
```
GET /api/v1/imports/
```

#### Exportação de Sucos
```
GET /api/v1/exports/juice
```

### 6.3 Formato de Resposta

```json
{
  "data": [
    {
      "Produto": "Vinho Tinto",
      "Quantidade": "156.789.431",
      "Ano": 2022
    },
    // ... outros registros
  ],
  "total": 25,
  "ano_filtro": 2022,
  "source_url": "http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_02&subopcao=subopt_01",
  "source": "web_scraping"
}
```

## 7. Análise de Dados

A classe `WineDataAnalyzer` fornece utilitários para análise dos dados obtidos:

- Limpeza e preparação de dados
- Cálculo de totais por categoria
- Comparação entre anos
- Identificação de produtos principais
- Comparação entre diferentes endpoints
- Geração de relatórios de análise

## 8. Conclusão

A VitiBrasil API resolve o problema de acesso programático aos dados de vitivinicultura brasileira, superando desafios de scraping e inconsistências nos dados de origem. A arquitetura modular e os mecanismos de fallback garantem alta disponibilidade e confiabilidade dos dados, mesmo quando há problemas no site de origem.

O projeto continua em desenvolvimento, com planos para:
- Ampliar a cobertura de tipos de dados
- Implementar caches para melhorar a performance
- Adicionar visualizações integradas
- Desenvolver um painel de administração

## 9. Atualizações Recentes

### 9.1 Melhorias na Documentação Interativa

- Substituição da interface Swagger UI personalizada (/custom-docs) pela interface padrão do FastAPI (/docs)
- Correção de problemas de codificação UTF-8 em templates customizados
- Otimização da renderização de Markdown na documentação da API
- Simplificação da estrutura de arquivos estáticos

### 9.2 Modelo de Autenticação

A API adota um modelo de acesso aberto para promover o uso acadêmico e a democratização dos dados:

- **Endpoints públicos**: Todos os endpoints de consulta de dados são públicos, sem necessidade de autenticação
- **Infraestrutura de autenticação**: Sistema de autenticação OAuth2 implementado para uso futuro
- **Controle de acesso**: Preparado para restringir operações administrativas ou de modificação quando necessário

### 9.3 Outras Melhorias

- Padronização do formato OpenAPI para versão 3.0.0
- Tratamento de exceções melhorado com logging detalhado
- Endpoint de diagnóstico (/debug/openapi) para verificação do schema OpenAPI
- Configurações personalizadas de Swagger UI para melhor experiência do usuário

## 10. Referências

- [Embrapa VitiBrasil](http://vitibrasil.cnpuv.embrapa.br/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Beautiful Soup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Swagger UI Documentation](https://swagger.io/tools/swagger-ui/)
- https://excalidraw.com/#json=x1k7UaBZE6iPtxbXyFfkA,QZc81REYTBitIVDsFZ84XQ

## 11. Otimizações de Performance

### 11.1 Sistema de Cache

A API implementa múltiplas camadas de cache para melhorar o desempenho:

1. **Cache de Resultados In-Memory**: 
   - Resultados de operações custosas (como web scraping) são cacheados em memória
   - TTL (Time-To-Live) configurável por endpoint
   - Reduz significativamente o tempo de resposta para consultas repetidas

2. **Cache HTTP**:
   - Headers HTTP (Cache-Control, ETag, Expires) implementados automaticamente
   - Permite que browsers e proxies façam cache das respostas
   - Reduz a carga no servidor e melhora a experiência do usuário

3. **Endpoints de Gerenciamento**:
   - `/api/v1/cache/info`: Mostra estatísticas do cache
   - `/api/v1/cache/clear`: Limpa o cache (útil para testes e quando há atualizações de dados)
   - `/api/v1/cache/test`: Demonstra a diferença de performance entre respostas cacheadas e não-cacheadas

A implementação melhora drasticamente o desempenho para dados que não mudam frequentemente, como estatísticas históricas de produção, importação e exportação.