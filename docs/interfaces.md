# VitiBrasil API - Core Interfaces

Este documento descreve as principais interfaces do sistema VitiBrasil API, suas responsabilidades e como utilizá-las adequadamente em diferentes contextos.

## 1. Interfaces de Validação

### 1.1 `Validator`

Interface base para todos os validadores do sistema.

```python
class Validator(Generic[T], ABC):
    @abstractmethod
    def validate(self, data: T) -> ValidationResult:
        """
        Valida dados de um tipo específico.
        
        Args:
            data: Dados a serem validados
            
        Returns:
            Resultado da validação contendo problemas encontrados
        """
        pass
```

#### Implementações Disponíveis:
- `StringValidator`: Validação de strings (comprimento, padrões, valores permitidos)
- `NumericValidator`: Validação de números (min/max, inteiros, positivos)
- `DateValidator`: Validação de datas (formato, range de datas)
- `DictValidator`: Validação de dicionários com schema definido
- `ListValidator`: Validação de listas (tamanho, unicidade, validação de itens)
- `DataFrameValidator`: Validação de DataFrames do pandas

#### Exemplo de Uso:
```python
validator = StringValidator(
    field_name="nome_produto", 
    min_length=3, 
    pattern=r'^[a-zA-Z\s]+$'
)
result = validator.validate("Cabernet Sauvignon")
if result.is_valid:
    print("Dados válidos!")
else:
    print(f"Problemas encontrados: {len(result.issues)}")
    for issue in result.issues:
        print(f"- {issue}")
```

### 1.2 `ValidationResult`

Classe que representa o resultado de uma validação.

```python
class ValidationResult:
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        
    def add_issue(self, issue: ValidationIssue) -> None:
        """Adiciona um problema ao resultado da validação."""
        self.issues.append(issue)
        
    @property
    def is_valid(self) -> bool:
        """Verifica se não há erros críticos no resultado."""
        return not any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL) 
            for issue in self.issues
        )
```

#### Métodos Principais:
- `add_issue(issue)`: Adiciona um problema ao resultado
- `add_issues(issues)`: Adiciona múltiplos problemas
- `is_valid`: Propriedade que verifica se não há erros críticos
- `get_issues_by_severity(severity)`: Filtra problemas por severidade
- `get_issues_by_field(field)`: Filtra problemas por campo

### 1.3 `Normalizer`

Interface para normalizadores de dados.

```python
class Normalizer(Generic[T, U], ABC):
    @abstractmethod
    def normalize(self, data: T) -> Tuple[U, ValidationResult]:
        """
        Normaliza dados de um tipo para outro, validando no processo.
        
        Args:
            data: Dados a serem normalizados
            
        Returns:
            Tupla contendo dados normalizados e resultado da validação
        """
        pass
```

#### Implementações Disponíveis:
- `StringNormalizer`: Normalização de strings (trim, case, acentos)
- `NumericNormalizer`: Normalização de valores numéricos
- `DateNormalizer`: Normalização de formatos de data
- `DictNormalizer`: Normalização de dicionários
- `DataFrameColumnNormalizer`: Normalização de colunas de DataFrame

## 2. Interfaces de Pipeline

### 2.1 `Transformer`

Interface base para transformadores de dados.

```python
class Transformer(Generic[T, U], ABC):
    @abstractmethod
    def transform(self, data: T) -> U:
        """
        Transforma dados de um tipo para outro.
        
        Args:
            data: Dados a serem transformados
            
        Returns:
            Dados transformados
        """
        pass
```

### 2.2 `ValidatingTransformer`

Interface para transformadores com validação integrada.

```python
class ValidatingTransformer(Generic[T, U], ABC):
    @abstractmethod
    def transform_and_validate(self, data: T) -> Tuple[U, ValidationResult]:
        """
        Transforma e valida dados.
        
        Args:
            data: Dados a serem transformados e validados
            
        Returns:
            Tupla com dados transformados e resultado da validação
        """
        pass
```

## 3. Interfaces de Cache

### 3.1 `CacheProvider`

Interface para provedores de cache.

```python
class CacheProvider(Generic[K, V], ABC):
    @abstractmethod
    def set(self, key: K, value: V, ttl_seconds: int = 3600) -> bool:
        """Armazena um valor no cache com tempo de expiração."""
        pass
        
    @abstractmethod
    def get(self, key: K) -> Optional[V]:
        """Obtém um valor do cache se existir e não tiver expirado."""
        pass
        
    @abstractmethod
    def delete(self, key: K) -> bool:
        """Remove um valor do cache."""
        pass
```

#### Implementações Disponíveis:
- `MemoryCacheProvider`: Cache em memória
- `FileCacheProvider`: Cache persistido em arquivos

## 4. Interfaces de Repository

### 4.1 `BaseRepository`

Interface base para repositórios de dados.

```python
class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_data(self, **kwargs) -> Dict[str, Any]:
        """Obtém dados conforme parâmetros fornecidos."""
        pass
```

### 4.2 `ScrapingRepository`

Interface específica para repositórios de scraping.

```python
class ScrapingRepository(BaseRepository[T]):
    @abstractmethod
    async def scrape_data(self, category: str, year: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Extrai dados via scraping de uma categoria específica."""
        pass
    
    @abstractmethod
    async def fallback_to_local(self, category: str, subcategory: Optional[str] = None, 
                              year: Optional[int] = None) -> Dict[str, Any]:
        """Tenta obter dados locais quando o scraping falha."""
        pass
```

## 5. Interfaces de Scraper

### 5.1 `BaseScraper`

Classe base para todos os scrapers especializados.

```python
class BaseScraper:
    def __init__(self):
        """Inicializa o scraper com configurações padrão."""
        self.session = self._create_session_with_retry()
        
    def _extract_table_data(self, soup) -> List[Dict[str, Any]]:
        """Extrai dados tabulares de uma página HTML."""
        pass
        
    def _fallback_to_csv(self, category, subcategory=None, year=None) -> pd.DataFrame:
        """Tenta obter dados de CSV local quando scraping falha."""
        pass
        
    def _get_available_years(self) -> List[int]:
        """Identifica anos disponíveis para extração."""
        pass
```

## 6. Diagrama de Relações

