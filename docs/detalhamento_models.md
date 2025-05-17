# Detalhamento Técnico: Models

Este documento fornece um detalhamento técnico aprofundado dos modelos e esquemas de dados da ViticultureAPI localizados na pasta `models`. Estes componentes definem as estruturas de dados, validações e formatos de resposta utilizados pela aplicação.

## 1. Modelo Base (`app/models/base.py`)

Este módulo define estruturas básicas compartilhadas por outros modelos da aplicação.

### 1.1. Resposta de Erro (`ErrorResponse`)

Define a estrutura padronizada para respostas de erro na API:

```python
class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    traceback: Optional[str] = None
```

Propriedades principais:
- **detail**: Mensagem descritiva do erro
- **status_code**: Código HTTP do erro (ex: 400, 404, 500)
- **code**: Código único do erro (opcional)
- **details**: Informações adicionais específicas do erro
- **timestamp**: Data/hora de quando o erro ocorreu
- **traceback**: Pilha de chamadas (apenas em ambiente de desenvolvimento)

Esta estrutura garante consistência nas respostas de erro em toda a aplicação.

### 1.2. Modelo Base (`BaseAPIModel`)

Classe base para todos os modelos da API:

```python
class BaseAPIModel(BaseModel):
    class Config:
        # Configurações padrão para todos os modelos
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }
        allow_population_by_field_name = True
        orm_mode = True
```

Características principais:
- **Configuração padronizada**: JSON encoders para tipos complexos
- **Flexibilidade de mapeamento**: Suporte para aliases de campos
- **Compatibilidade ORM**: Facilita conversão entre modelos e entidades de banco de dados

## 2. Modelos de Produção (`app/models/production.py`)

Define modelos relacionados aos dados de produção vitivinícola.

### 2.1. Registro de Produção (`ProductionRecord`)

Representa um registro individual de produção:

```python
class ProductionRecord(BaseAPIModel):
    produto: str
    quantidade: Optional[float] = Field(None, description="Quantidade em litros ou toneladas")
    unidade: Optional[str] = Field("L", description="Unidade de medida (L, ton)")
    ano: Optional[int] = None
    regiao: Optional[str] = None
    variedade: Optional[str] = None
    tipo: Optional[str] = None
```

### 2.2. Resposta de Produção (`ProductionResponse`)

Define a estrutura da resposta para endpoints de produção:

```python
class ProductionResponse(BaseAPIModel):
    data: List[ProductionRecord]
    total: int = Field(..., description="Número total de registros")
    ano_filtro: Optional[int] = Field(None, description="Ano filtrado, se aplicável")
    source_url: Optional[str] = Field(None, description="URL da fonte dos dados")
    source: str = Field("web_scraping", description="Fonte dos dados (web_scraping ou file)")
```

A estrutura inclui tanto os dados solicitados quanto metadados importantes sobre a origem e filtragem.

## 3. Modelos de Importação (`app/models/imports.py`)

Define modelos para os dados de importação de produtos vitivinícolas.

### 3.1. Registro de Importação (`ImportRecord`)

```python
class ImportRecord(BaseAPIModel):
    pais_origem: str
    quantidade: float
    valor_dolar: float
    preco_medio: Optional[float] = None
    ano: int
    categoria: Optional[str] = None
```

Características principais:
- **pais_origem**: País de onde o produto foi importado
- **quantidade**: Volume importado (em litros ou kg)
- **valor_dolar**: Valor total em dólares americanos
- **preco_medio**: Calculado automaticamente quando possível (valor/quantidade)
- **ano**: Ano da importação
- **categoria**: Tipo de produto (vinho, espumante, suco, etc.)

### 3.2. Resposta de Importação (`ImportResponse`)

```python
class ImportResponse(BaseAPIModel):
    data: List[ImportRecord]
    total: int
    ano_filtro: Optional[int] = None
    source_url: Optional[str] = None
    source: str = "web_scraping"
```

## 4. Modelos de Exportação (`app/models/exports.py`)

Similar aos modelos de importação, define estruturas para dados de exportação:

### 4.1. Registro de Exportação (`ExportRecord`)

```python
class ExportRecord(BaseAPIModel):
    pais_destino: str
    quantidade: float
    valor_dolar: float
    preco_medio: Optional[float] = None
    ano: int
    categoria: Optional[str] = None
```

### 4.2. Resposta de Exportação (`ExportResponse`)

```python
class ExportResponse(BaseAPIModel):
    data: List[ExportRecord]
    total: int
    ano_filtro: Optional[int] = None
    source_url: Optional[str] = None
    source: str = "web_scraping"
```

## 5. Modelos de Processamento (`app/models/processing.py`)

Define estruturas para dados de processamento industrial de uvas.

### 5.1. Registro de Processamento (`ProcessingRecord`)

```python
class ProcessingRecord(BaseAPIModel):
    variedade: str
    quantidade: float
    unidade: str = "kg"
    ano: int
    categoria: Optional[str] = None
    regiao: Optional[str] = None
```

Categorias possíveis incluem "vinifera", "american", "table" e "unclassified".

### 5.2. Resposta de Processamento (`ProcessingResponse`)

```python
class ProcessingResponse(BaseAPIModel):
    data: List[ProcessingRecord]
    total: int
    ano_filtro: Optional[int] = None
    categoria_filtro: Optional[str] = None
    source_url: Optional[str] = None
    source: str = "web_scraping"
```

## 6. Modelos de Comercialização (`app/models/commercialization.py`)

Define estruturas para dados de comercialização no mercado interno.

### 6.1. Registro de Comercialização (`CommercializationRecord`)

```python
class CommercializationRecord(BaseAPIModel):
    produto: str
    quantidade: float
    unidade: str = "L"
    ano: int
    tipo: Optional[str] = None
```

### 6.2. Resposta de Comercialização (`CommercializationResponse`)

```python
class CommercializationResponse(BaseAPIModel):
    data: List[CommercializationRecord]
    total: int
    ano_filtro: Optional[int] = None
    source_url: Optional[str] = None
    source: str = "web_scraping"
```

## 7. Modelos de Autenticação (`app/models/auth.py`)

Define modelos para o sistema de autenticação:

### 7.1. Token (`Token`)

```python
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 60 * 24 * 8 * 60  # 8 dias em minutos
```

### 7.2. Payload do Token (`TokenPayload`)

```python
class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
```

### 7.3. Usuário (`User`)

```python
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False
```

## 8. Modelos de Cache (`app/models/cache.py`)

Define estruturas para endpoints de gerenciamento do cache:

### 8.1. Informações do Cache (`CacheInfo`)

```python
class CacheInfo(BaseAPIModel):
    total_entries: int
    valid_entries: int
    expired_entries: int
    memory_usage: Optional[int] = None
    provider: str
    entries: List[Dict[str, Any]]
```

### 8.2. Resultado de Benchmark (`BenchmarkResult`)

```python
class BenchmarkResult(BaseAPIModel):
    cached_time_ms: float
    uncached_time_ms: float
    speedup_factor: float
    cached_response: Any
    uncached_response: Any
```

## 9. Integração com Pydantic

Todos os modelos se beneficiam das funcionalidades do Pydantic:

1. **Validação automática**: Os dados são validados no momento da deserialização
2. **Conversão de tipos**: Strings são convertidas para tipos apropriados automaticamente
3. **Documentação OpenAPI**: Os modelos geram automaticamente schemas para a documentação Swagger/OpenAPI
4. **Validação customizada**: Funções de validação com decorador `@validator`

Exemplo de validação customizada:

```python
class ImportRecord(BaseAPIModel):
    # ...campos definidos anteriormente...

    @validator("preco_medio", pre=True, always=True)
    def calculate_price(cls, v, values):
        if v is not None:
            return v
            
        quantidade = values.get("quantidade")
        valor = values.get("valor_dolar")
        
        if quantidade and valor and quantidade > 0:
            return round(valor / quantidade, 2)
        return None
```

## 10. Benefícios da Abordagem Baseada em Modelos

1. **Consistência**: Formato padronizado para respostas da API
2. **Validação**: Dados validados automaticamente na serialização/deserialização
3. **Documentação**: Geração automática de schemas OpenAPI
4. **Conversão de tipos**: Tratamento automático de tipos de dados
5. **Extensibilidade**: Fácil adicionar novos modelos ou campos

## 11. Schemas (`app/schemas`)

A pasta `schemas` contém definições de estruturas de dados utilizadas especificamente para validação de requisições e respostas da API. Enquanto os modelos em `models/` são utilizados principalmente para a estrutura de resposta completa, os schemas são focados em estruturas de dados específicas que podem ser reutilizadas em diferentes contextos.

### 11.1. Schemas de Produção (`production.py`)

Define schemas relacionados à produção vinícola:

```python
class WineProduction(BaseModel):
    produto: str = Field(..., description="Nome do produto")
    quantidade: float = Field(..., description="Quantidade em litros")
    ano: Optional[int] = Field(None, description="Ano de referência")
    
    class Config:
        schema_extra = {
            "example": {
                "produto": "Vinho tinto de mesa",
                "quantidade": 123456.78,
                "ano": 2022
            }
        }
```

A classe `WineProduction` representa um registro individual de produção vinícola com:
- **produto**: Nome do produto (vinhos, sucos, etc.)
- **quantidade**: Volume produzido em litros
- **ano**: Ano de referência da produção (opcional)

A configuração `schema_extra` fornece um exemplo para a documentação OpenAPI/Swagger.

```python
class WineProductionList(BaseModel):
    data: List[WineProduction]
    total: int
    ano: Optional[int] = None
```

A classe `WineProductionList` representa uma coleção de registros de produção:
- **data**: Lista de registros de produção
- **total**: Número total de registros
- **ano**: Ano de referência do conjunto de dados (opcional)

### 11.2. Diferença entre Models e Schemas

No contexto da aplicação:

1. **Models (`app/models/`)**: 
   - Representam estruturas completas de dados
   - Definem o formato das respostas da API
   - Incluem todos os metadados e campos necessários
   - São usados principalmente para serialização de respostas

2. **Schemas (`app/schemas/`)**:
   - Representam estruturas atômicas de dados
   - Focam na validação de dados de entrada
   - São mais simples e reutilizáveis
   - Podem ser compostos para formar estruturas mais complexas
   - Facilitam a validação de requisições

### 11.3. Integração com FastAPI

Os schemas são particularmente úteis com FastAPI para:

1. **Validação de Request Body**:
   ```python
   @router.post("/production")
   async def create_production(production: WineProduction):
       # Os dados já chegam validados pelo Pydantic
   ```

2. **Documentação automática**:
   - FastAPI usa os schemas para gerar exemplos na documentação Swagger/OpenAPI
   - Descrições de campos são exibidas na interface

3. **Conversão e validação automática**:
   - Strings são convertidas para tipos apropriados
   - Validações de campo são aplicadas automaticamente
   - Erros de validação geram respostas 422 (Unprocessable Entity) com detalhes claros

### 11.4. Boas Práticas Utilizadas

1. **Documentação em Fields**: Uso do parametro `description` em cada Field
2. **Exemplos**: Definição de exemplos via `schema_extra` para melhor documentação
3. **Tipagem Explícita**: Uso consistente de type hints para melhor IDE support
4. **Valores Padrão Sensatos**: Definição de defaults apropriados quando relevante
5. **Campos Opcionais Claros**: Uso de `Optional[]` para campos não obrigatórios
