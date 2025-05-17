# Detalhamento Técnico: Core e Componentes Fundamentais

Este documento fornece um detalhamento técnico aprofundado dos componentes fundamentais da ViticultureAPI localizados na pasta `core` e suas subpastas. Estes componentes formam a infraestrutura básica na qual toda a aplicação é construída.

## 1. Sistema de Cache (`app/core/cache/`)

O sistema de cache implementa uma abordagem robusta de caching em múltiplas camadas para otimizar o desempenho da API.

### 1.1. Decorador de Cache (`cache/decorator.py`)

Este módulo fornece o decorador `@cache_result` que permite cachear facilmente os resultados de funções assíncronas:

```python
@cache_result(ttl_seconds=3600, tags=["production"], provider="memory")
async def get_production_data(year):
    # Código que busca dados...
    return data
```

Características principais:
- **Configuração flexível**: TTL (time-to-live), tags, provider
- **Sobrecarga amigável**: Pode ser usado como `@cache_result` ou `@cache_result()`
- **Suporte a tags**: Permite invalidar múltiplas chaves de cache por tag
- **Personalização de chaves**: Controle sobre como as chaves são geradas
- **Medição de performance**: Recursos opcionais de timing para análise de desempenho
- **Tratamento de erros**: Proteção contra falhas no cache que possam afetar funcionalidades

O decorador suporta múltiplas sobrecargas e inclui robustas verificações de tipo para evitar problemas durante a execução.

### 1.2. Interface de Cache (`cache/interface.py`)

Define interfaces comuns que todos os provedores de cache devem implementar:

```python
class CacheProvider(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any: pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None: pass
    
    @abstractmethod
    async def delete(self, key: str) -> None: pass
    
    @abstractmethod
    async def clear(self) -> None: pass
```

A interface `TaggedCacheProvider` estende esta interface básica com suporte adicional para operações baseadas em tags.

### 1.3. Fábrica de Cache (`cache/factory.py`)

Implementa o padrão de design Factory para criar e gerenciar instâncias de provedores de cache:

```python
class CacheFactory:
    _instance = None
    _providers = {}
    _default_provider = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    # Outros métodos...
```

Funcionalidades principais:
- **Singleton**: Garante uma única instância da fábrica em toda a aplicação
- **Lazy loading**: Provedores são inicializados apenas quando necessário
- **Configuração via .env**: Permite configurar provedores através de variáveis de ambiente
- **Fallback**: Sistema de fallback para casos em que o provedor primário falha

### 1.4. Provedores de Cache

O sistema inclui múltiplos provedores para diferentes cenários:

1. **MemoryCacheProvider** (`cache/memory.py`): Armazenamento em memória para acesso ultra-rápido
2. **RedisCacheProvider** (`cache/redis.py`): Implementação baseada em Redis para persistência e distribuição
3. **FileCacheProvider** (`cache/file.py`): Armazenamento em arquivo para persistência simples

Cada implementação segue as interfaces comuns, permitindo substituição transparente.

## 2. Sistema de Validação (`app/core/validation/`)

O sistema de validação fornece uma estrutura robusta para validar dados em diferentes níveis da aplicação.

### 2.1. Interfaces de Validação (`validation/interface.py`)

Define as abstrações fundamentais do sistema de validação:

1. **ValidationSeverity**: Enum para níveis de severidade (INFO, WARNING, ERROR, CRITICAL)
2. **ValidationIssue**: Representa um problema específico encontrado durante validação
3. **ValidationResult**: Contém múltiplos issues e métodos para análise de resultados
4. **Validator**: Interface base para todos os validadores

```python
class ValidationResult:
    def __init__(self):
        self.issues: List[ValidationIssue] = []
    
    @property
    def is_valid(self) -> bool:
        return not any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL) 
            for issue in self.issues
        )
        
    # Outros métodos...
```

A função utilitária `validate_common` implementa verificações básicas compartilhadas entre validadores.

### 2.2. Validadores Específicos (`validation/validators.py`)

Implementa validadores para diferentes tipos de dados:

1. **StringValidator**: Valida strings com base em comprimento, padrão regex, valores permitidos, etc.
2. **NumericValidator**: Valida números com base em valores mínimo/máximo, tipo (int/float)
3. **DateValidator**: Valida datas contra intervalos e formatos específicos
4. **ListValidator**: Valida listas e seus elementos contra outro validador
5. **DictValidator**: Valida dicionários contra um schema especificado
6. **DataFrameValidator**: Valida DataFrames pandas por coluna e conteúdo

Cada validador segue o padrão de composição, permitindo construir regras complexas a partir de componentes simples.

### 2.3. Normalizadores (`validation/normalizers.py`)

Complementa os validadores com capacidade de transformar dados:

1. **StringNormalizer**: Normaliza strings (strip, uppercase, remoção de acentos)
2. **NumericNormalizer**: Converte strings para números, formata decimais
3. **DateNormalizer**: Converte strings para datas, padroniza formatos

Os normalizadores combinam validação e transformação, garantindo dados limpos e válidos.

### 2.4. Relatórios de Validação (`validation/reporter.py`)

Fornece mecanismos para gerar e armazenar relatórios de validação:

1. **ValidationReporter**: Gera relatórios em JSON, CSV
2. **DataQualityMonitor**: Monitora tendências de qualidade de dados ao longo do tempo

```python
class ValidationReporter:
    def __init__(self, name: str):
        self.name = name
        
    def to_json(self, result: ValidationResult, filepath: Optional[str] = None) -> str:
        # Implementação...
```

### 2.5. Integração com Pipeline (`validation/pipeline.py`)

Integra validação ao framework de pipeline da aplicação:

1. **ValidatingPipelineTransformer**: Transformer que valida dados
2. **NormalizingPipelineTransformer**: Transformer que normaliza e valida
3. **ValidationPipelineFactory**: Fábrica para criar transformers de validação

## 3. Sistema de Logging (`app/core/logging.py`)

Implementa um sistema de logging avançado com suporte a:

1. **Formatação JSON**: Logs estruturados para fácil análise
2. **Contexto**: Adição dinâmica de campos de contexto aos logs
3. **Configuração flexível**: Suporte a arquivo, console, níveis configuráveis
4. **Correlação**: Rastreamento de requisições através de request_id

```python
class LogContext:
    _context = contextvars.ContextVar("log_context", default={})
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        context = cls._context.get()
        cls._context.set({**context, key: value})
        
    # Outros métodos...
```

A função `setup_logging` configura todo o sistema de logging com base em parâmetros e variáveis de ambiente.

## 4. Middlewares (`app/core/middleware.py`)

Implementa middlewares ASGI para funcionalidades transversais:

### 4.1. CacheControlMiddleware

Adiciona headers HTTP de cache às respostas:

```python
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Adicionar headers de cache apropriados com base no caminho e método
        # ...
        
        return response
```

Recursos principais:
- Configuração de `Cache-Control` por padrão para GETs
- Adição de `Expires` e `ETag` headers
- Configuração personalizada por caminho de URL
- Lista de exclusão para endpoints que não devem ser cacheados

### 4.2. ErrorHandlerMiddleware

Middleware para tratamento centralizado de exceções:

```python
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # Converter para exceção padronizada e retornar resposta JSON
            # ...
```

Benefícios:
- Tratamento consistente de erros em toda a aplicação
- Respostas JSON padronizadas para exceções
- Logging automático de erros com detalhes contextuais
- Modo de desenvolvimento com tracebacks detalhados

### 4.3. RequestLoggingMiddleware

Registra informações detalhadas sobre todas as requisições:

```python
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Registrar início da requisição com detalhes
        # Processar requisição e calcular tempo de resposta
        # Registrar detalhes da resposta
        # ...
```

Informações registradas:
- Método HTTP, caminho, parâmetros de consulta
- IP do cliente, User-Agent
- Tempo de processamento
- Código de status, tipo de conteúdo, tamanho da resposta

### 4.4. RequestIDMiddleware

Garante que todas as requisições tenham um ID único para rastreamento:

```python
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar ou gerar request_id
        # Adicionar request_id à resposta
        # ...
```

A função `setup_middlewares` configura todos os middlewares na ordem correta de execução.

## 5. Tratamento de Exceções (`app/core/exceptions.py`)

Implementa um sistema hierárquico de exceções personalizadas:

1. **BaseAppException**: Classe base para todas as exceções da aplicação
2. **Exceções HTTP**: Mapeadas para códigos de status HTTP (400, 401, 403, 404, 500, 503)
3. **ValidationException**: Específica para erros de validação com detalhes por campo

```python
class BaseAppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        # Inicialização com detalhes para diagnóstico
        # ...
        
    def to_dict(self) -> Dict[str, Any]:
        # Converter exceção para resposta JSON padronizada
        # ...
```

A função utilitária `handle_exception` converte exceções Python genéricas em exceções padronizadas da aplicação.

## 6. Configuração (`app/core/config.py`)

Gerencia configurações da aplicação através de:

1. **Classe Settings**: Modelo Pydantic para configuração com valores padrão e validação
2. **Carregamento .env**: Integração com python-dotenv para variáveis de ambiente
3. **Validação de valores**: Garantia de valores válidos e detecção de configurações incorretas

```python
class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ViticultureAPI"
    
    # Configurações de segurança
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 dias
    
    # Outras configurações...
    
    class Config:
        case_sensitive = True
        env_file = ".env"
```

## 7. Sistema de Pipeline (`app/core/pipeline.py`)

Implementa um framework de ETL (Extract, Transform, Load) para processamento de dados:

1. **Extractors**: Componentes para extrair dados de diversas fontes
2. **Transformers**: Componentes para transformar e processar dados
3. **Loaders**: Componentes para persistir resultados processados

```python
class Pipeline:
    def __init__(self, name: Optional[str] = None):
        self.name = name or str(uuid.uuid4())
        self.extractors: List[Extractor] = []
        self.transformers: List[Transformer] = []
        self.loaders: List[Loader] = []
        
    async def execute(self) -> Dict[str, Any]:
        # Extrair dados
        # Aplicar transformações
        # Carregar resultados
        # ...
```

Componentes específicos incluem:
- **CSVExtractor**: Extrai dados de arquivos CSV
- **DataFrameTransformer**: Transforma DataFrames Pandas
- **DataFrameToCSVLoader**: Persiste DataFrames em CSV

## 8. Utilitários (`app/core/utils.py`)

Fornece funções utilitárias para várias partes da aplicação:

### 8.1. clean_navigation_arrows

Remove setas de navegação que podem aparecer em dados extraídos por scraping:

```python
def clean_navigation_arrows(data_list):
    """
    Remove navigation arrow entries from scraped data results and fix data structure.
    
    1. Removes navigation arrow entries ("«‹›»")
    2. Fixes duplicate quantity fields
    3. Cleans navigation arrows from quantity values
    """
    # Implementação...
```

### 8.2. safe_float_conversion

Converte valores para float de forma segura, lidando com formatos problemáticos:

```python
def safe_float_conversion(value, default=0.0):
    """
    Safely convert a value to float, handling navigation arrows and other invalid formats.
    """
    # Implementação...
```

## 9. Segurança (`app/core/security.py`)

Implementa funcionalidades de segurança:

1. **Geração de token**: Criação de tokens JWT para autenticação
2. **Verificação de token**: Middleware de dependência para proteger endpoints
3. **Configuração segura**: Gerenciamento seguro de chaves e credenciais

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # Criar token JWT com payload e expiração
    # ...

async def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    # Verificar e decodificar token JWT
    # ...
```

## 10. Hypermedia (`app/core/hypermedia.py`)

Implementa o princípio HATEOAS para tornar a API verdadeiramente RESTful:

```python
def add_links(response: Dict[str, Any], resource_path: str, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Adiciona links HATEOAS a uma resposta.
    """
    # Adicionar links para o próprio recurso, recursos relacionados, etc.
    # ...
```

Propriedades principais:
1. **Links contextuais**: Gerados com base no tipo de recurso
2. **Navegação relacionada**: Links para outros recursos pertinentes
3. **Navegação temporal**: Links para anos anteriores/posteriores quando aplicável
4. **Tratamento de tipo seguro**: Implementação robusta contra erros de tipo

A estrutura de links segue o formato HAL (Hypertext Application Language) para máxima compatibilidade com clientes REST.
