# VitiBrasil API - Arquitetura do Sistema

Este documento descreve a arquitetura geral do sistema VitiBrasil API, apresentando seus componentes principais, fluxos de dados e interações entre módulos.

## 1. Visão Geral da Arquitetura

O VitiBrasil API é uma aplicação baseada em FastAPI que fornece dados estruturados sobre a indústria vitivinícola brasileira. A arquitetura do sistema é organizada em camadas, seguindo padrões de Clean Architecture e princípios SOLID.

```mermaid
graph TB
    subgraph "API Layer"
        A[API Endpoints]
        MW[Middlewares]
    end
    
    subgraph "Service Layer"
        SVC[Services]
        TRANS[Transformers]
        VALID[Validation]
    end
    
    subgraph "Repository Layer"
        REPO[Repositories]
        SCRAPER[Scrapers]
    end
    
    subgraph "Core"
        PIPE[Pipeline]
        CACHE[Cache]
        LOG[Logging]
        EX[Exceptions]
    end
    
    subgraph "Data Sources"
        WEB[Web Scraping]
        CSV[CSV Files]
        EXTERN[External APIs]
    end
    
    A --> SVC
    MW --> A
    SVC --> TRANS
    SVC --> VALID
    SVC --> REPO
    REPO --> SCRAPER
    SCRAPER --> WEB
    REPO --> CSV
    REPO --> EXTERN
    TRANS --> PIPE
    VALID --> PIPE
    PIPE --> CACHE
    PIPE --> LOG
    PIPE --> EX
```

## 2. Componentes Principais

### 2.1. API Layer
- **Endpoints**: Interfaces REST para acesso aos dados
- **Middlewares**: Componentes para processamento de requisições (cache, logs, autenticação)

### 2.2. Service Layer
- **Services**: Lógica de negócio e orquestração de dados
- **Transformers**: Conversão e normalização de dados
- **Validation**: Validação de dados de entrada e saída

### 2.3. Repository Layer
- **Repositories**: Acesso a dados de diferentes fontes
- **Scrapers**: Extração de dados de sites específicos

### 2.4. Core
- **Pipeline**: Framework para processamento ETL de dados
- **Cache**: Sistema de cache para otimizar desempenho
- **Logging**: Sistema de logging para monitoramento
- **Exceptions**: Tratamento padronizado de exceções

### 2.5. Data Sources
- **Web Scraping**: Extração de dados de sites governamentais
- **CSV Files**: Arquivos locais para fallback e dados históricos
- **External APIs**: Integração com APIs externas

## 3. Fluxos de Dados Principais

### 3.1. Fluxo de Requisição API

```mermaid
sequenceDiagram
    participant C as Cliente API
    participant E as Endpoint
    participant S as Service
    participant R as Repository
    participant DS as Data Source
    
    C->>E: Requisita dados (GET)
    activate E
    E->>S: Solicita processamento
    activate S
    
    alt Cache disponível
        S->>S: Recupera do cache
    else Cache indisponível
        S->>R: Solicita dados
        activate R
        R->>DS: Extrai dados
        DS->>R: Retorna dados brutos
        R->>S: Retorna dados estruturados
        deactivate R
        S->>S: Armazena no cache
    end
    
    S->>E: Retorna dados processados
    deactivate S
    E->>C: Resposta JSON
    deactivate E
```

### 3.2. Fluxo de Processamento ETL

```mermaid
flowchart TD
    A[Dados Brutos] -->|Extração| B[Extractor]
    B -->|Dados extraídos| C[Transformer]
    C -->|Dados normalizados| D[Validator]
    D -->|Dados validados| E[Transformer]
    E -->|Dados transformados| F[Loader]
    F -->|Persistência| G[Dados Processados]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#bbf,stroke:#333,stroke-width:2px
```

## 4. Sistema de Validação

O sistema de validação é um componente crítico que garante a integridade dos dados processados:

```mermaid
classDiagram
    class Validator {
        <<interface>>
        +validate(data) ValidationResult
    }
    
    class ValidationResult {
        -issues: List[ValidationIssue]
        +add_issue(issue)
        +is_valid: bool
    }
    
    class ValidationIssue {
        +field: string
        +message: string
        +severity: ValidationSeverity
    }
    
    class StringValidator {
        +min_length: int
        +max_length: int
        +pattern: regex
        +validate(data) ValidationResult
    }
    
    class NumericValidator {
        +min_value: float
        +max_value: float
        +is_integer: bool
        +validate(data) ValidationResult
    }
    
    class DictValidator {
        +schema: Dict[str, Validator]
        +validate(data) ValidationResult
    }
    
    Validator <|-- StringValidator
    Validator <|-- NumericValidator
    Validator <|-- DictValidator
    Validator ..> ValidationResult
    ValidationResult o-- ValidationIssue
```

## 5. Integração Pipeline e Validação

```mermaid
classDiagram
    class Pipeline {
        +add_extractor(extractor)
        +add_transformer(transformer)
        +add_loader(loader)
        +execute() result
    }
    
    class Transformer {
        <<interface>>
        +transform(data) transformed_data
    }
    
    class ValidatingTransformer {
        +validator: Validator
        +transform(data) transformed_data
        +transform_and_validate(data) Tuple[data, result]
    }
    
    class Validator {
        <<interface>>
        +validate(data) ValidationResult
    }
    
    Transformer <|-- ValidatingTransformer
    ValidatingTransformer --> Validator
    Pipeline o-- Transformer
```

## 6. Tecnologias Utilizadas

- **Framework Web**: FastAPI
- **Scraping**: BeautifulSoup, Requests
- **Processamento de Dados**: Pandas
- **Validação**: Sistema customizado de validação
- **Documentação**: OpenAPI (Swagger)
- **Logging**: Loggers com formatação JSON
- **Cache**: Sistema In-memory e baseado em arquivos
