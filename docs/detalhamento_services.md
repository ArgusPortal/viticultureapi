# Detalhamento Técnico: Módulo de Serviços

Este documento fornece um detalhamento técnico da camada de serviços da ViticultureAPI, explicando a implementação dos padrões de design e a organização dos componentes de processamento de dados.

## 1. Estrutura dos Serviços (`app/services`)

A pasta `services` implementa a camada de serviços da aplicação, responsável pela lógica de negócios que conecta os modelos de dados aos repositórios. Esta camada é crucial para manter a separação de responsabilidades e facilitar a manutenção do código.

### 1.1. Organização do Módulo

```
app/services/
├── __init__.py           # Exports das interfaces e implementações principais
├── interfaces.py         # Interfaces base para todos os serviços
├── data_service.py       # Serviço para processamento geral de dados
├── data_transformer.py   # Serviço para transformação de dados
├── base_service.py       # Implementação base para serviços
├── strategies/           # Implementações do padrão Strategy
│   ├── __init__.py       # Exports das estratégias disponíveis
│   ├── base.py           # Interfaces base para estratégias
│   ├── cleaning_strategies.py    # Estratégias de limpeza
│   └── enrichment_strategies.py  # Estratégias de enriquecimento
└── transformers/         # Implementações de transformadores
    ├── __init__.py       # Exports dos transformers
    ├── base.py           # Classes base para transformadores
    └── data_transformers.py      # Transformadores específicos
```

Esta organização facilita:
- Localização de código relacionado
- Extensão do sistema com novas estratégias e transformadores
- Separação de responsabilidades entre componentes
- Reutilização de lógica comum

## 2. Padrões de Design Implementados

### 2.1. Padrão Strategy

O módulo implementa o padrão Strategy para encapsular diferentes algoritmos de processamento de dados, permitindo que sejam intercambiáveis conforme a necessidade.

#### 2.1.1. Interface Base (`strategies/base.py`)

```python
class ProcessingStrategy(ABC):
    """Interface base para estratégias de processamento."""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Processa os dados de acordo com a estratégia implementada.
        
        Args:
            data: Dados a serem processados
            
        Returns:
            Dados processados
        """
        pass
```

A partir desta interface base, são derivadas interfaces específicas:

1. **CleaningStrategy**: Para algoritmos de limpeza de dados
2. **EnrichmentStrategy**: Para algoritmos de enriquecimento de dados
3. **ValidationStrategy**: Para algoritmos de validação de dados

#### 2.1.2. Estratégias de Limpeza (`cleaning_strategies.py`)

```python
class NavigationArrowsCleaningStrategy(CleaningStrategy):
    """Estratégia para remover setas de navegação e corrigir estrutura de dados."""
    
    def __init__(self):
        self.nav_arrows_pattern = re.compile(r'[«‹›»]')
    
    def clean(self, data: Any) -> Any:
        """
        Remove entradas com setas de navegação e campos duplicados.
        
        Args:
            data: Dados a serem limpos (lista de dicionários esperada)
            
        Returns:
            Dados limpos
        """
        if not isinstance(data, list):
            logger.warning(f"NavigationArrowsCleaningStrategy esperava lista, recebeu {type(data)}")
            return data
        
        cleaned_data = []
        removed_count = 0
        fixed_fields_count = 0
        
        for item in data:
            if not isinstance(item, dict):
                cleaned_data.append(item)
                continue
                
            # Skip navigation arrow entries
            if any("«‹›»" in str(value) for key, value in item.items() 
                  if key.lower() in ["navegação", "navigation"]):
                removed_count += 1
                continue
                
            # Clean item
            cleaned_item = {}
            for key, value in item.items():
                if isinstance(value, str):
                    cleaned_value = self.nav_arrows_pattern.sub('', value).strip()
                    cleaned_item[key] = cleaned_value
                else:
                    cleaned_item[key] = value
                    
            # Fix duplicate fields
            if "Quantidade (L.)" in cleaned_item and "Quantidade" in cleaned_item:
                cleaned_item.pop("Quantidade", None)
                fixed_fields_count += 1
                
            cleaned_data.append(cleaned_item)
        
        logger.debug(f"Removed {removed_count} navigation items, fixed {fixed_fields_count} duplicate fields")
        return cleaned_data
```

Esta estratégia específica resolve um problema comum nos dados extraídos: a presença de caracteres de setas de navegação que interferem na análise dos dados.

### 2.2. Padrão Composite

O módulo também implementa o padrão Composite para estratégias, permitindo combinar múltiplas estratégias em uma única unidade:

```python
class CompositeStrategy(ProcessingStrategy):
    """Estratégia que combina múltiplas estratégias sequencialmente."""
    
    def __init__(self, strategies: List[ProcessingStrategy]):
        """
        Inicializa com lista de estratégias.
        
        Args:
            strategies: Lista de estratégias a serem aplicadas em sequência
        """
        self.strategies = strategies
    
    def process(self, data: Any) -> Any:
        """
        Aplica todas as estratégias sequencialmente.
        
        Args:
            data: Dados a serem processados
            
        Returns:
            Dados após aplicação de todas as estratégias
        """
        result = data
        for strategy in self.strategies:
            result = strategy.process(result)
        return result
```

Esta implementação permite encadear processamentos, como limpar os dados, depois validá-los e, finalmente, enriquecê-los, tudo em uma única chamada.

### 2.3. Padrão Transformer

O módulo de transformadores implementa uma variação do padrão Builder, focado na transformação progressiva de dados:

```python
class BaseTransformer:
    """Classe base para transformadores de dados."""
    
    def transform(self, data: Any) -> Any:
        """
        Método principal que transforma os dados.
        
        Args:
            data: Dados a serem transformados
            
        Returns:
            Dados transformados
        """
        logger.debug(f"Transformando dados com {self.__class__.__name__}")
        return self._transform_data(data)
    
    def _transform_data(self, data: Any) -> Any:
        """
        Implementação específica da transformação a ser sobrescrita pelas subclasses.
        
        Args:
            data: Dados a serem transformados
            
        Returns:
            Dados transformados
        """
        # Implementação padrão: retorna os dados sem modificação
        return data
```

## 3. Implementações Específicas

### 3.1. Limpeza de Dados

#### 3.1.1. NavigationArrowsCleaner

Este transformador especializado remove artefatos de navegação dos dados extraídos por scraping:

```python
class NavigationArrowsCleaner(BaseTransformer):
    """Transformador que remove setas de navegação dos dados."""
    
    def __init__(self):
        self.nav_arrows_pattern = re.compile(r'[«‹›»]')
    
    def _transform_data(self, data: Any) -> Any:
        """
        Remove entradas com setas de navegação e campos duplicados.
        
        Args:
            data: Dados a serem transformados (lista de dicionários esperada)
            
        Returns:
            Dados limpos
        """
        if not isinstance(data, list):
            logger.warning(f"NavigationArrowsCleaner esperava lista, recebeu {type(data)}")
            return data
        
        cleaned_data = []
        removed_count = 0
        fixed_fields_count = 0
        cleaned_values_count = 0
        
        for item in data:
            # Skip items that match the navigation arrows pattern
            if (isinstance(item, dict) and 
                item.get("Produto", "") == "" and 
                "«‹›»" in str(item.get("Quantidade (L.)", ""))):
                removed_count += 1
                continue
            
            # Resto da implementação para tratar outros casos
            # ...
            
        logger.debug(f"Cleaned data: removed {removed_count} items, fixed {fixed_fields_count} fields")
        return cleaned_data
```

Este transformador é crucial para a qualidade dos dados, pois:
1. Remove entradas que são puramente de navegação e não contêm dados reais
2. Limpa caracteres especiais que poderiam causar problemas na análise
3. Resolve duplicidade de campos com diferentes formatos

### 3.2. Limpeza de Valores Vazios

Outra estratégia implementada é para tratamento de valores vazios nos dados:

```python
class EmptyValueCleaningStrategy(CleaningStrategy):
    """Estratégia para tratar valores vazios em dados."""
    
    def __init__(self, default_str: str = "", default_num: float = 0.0):
        """
        Inicializa a estratégia com valores padrão.
        
        Args:
            default_str: Valor padrão para strings vazias
            default_num: Valor padrão para números vazios
        """
        self.default_str = default_str
        self.default_num = default_num
        
    def clean(self, data: Any) -> Any:
        """
        Substitui valores vazios por valores padrão.
        
        Args:
            data: Dados a serem limpos
            
        Returns:
            Dados com valores vazios tratados
        """
        # Implementação para substituir valores vazios
        # ...
```

Esta estratégia garante que não haja valores nulos ou vazios nos dados processados, melhorando a consistência para análises posteriores.

## 4. Interface de Serviços

A arquitetura define interfaces claras para os serviços, facilitando a implementação consistente e testável:

```python
class BaseService(ABC):
    """Interface base para todos os serviços."""
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Executa a funcionalidade principal do serviço."""
        pass

class DataService(BaseService):
    """Interface para serviços de processamento de dados."""
    
    @abstractmethod
    async def get_data(self, filters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Obtém dados com base em filtros opcionais.
        
        Args:
            filters: Filtros para aplicar aos dados
            
        Returns:
            Dados processados
        """
        pass
```

## 5. Integração com Sistema de Cache

Os serviços se integram perfeitamente com o sistema de cache da aplicação, garantindo resposta rápida para dados que não mudam frequentemente:

```python
class CachedDataService(DataService):
    """Implementação de serviço com cache integrado."""
    
    def __init__(self, repository, cache_ttl=3600):
        self.repository = repository
        self.cache_ttl = cache_ttl
    
    @cache_result(ttl_seconds=3600)
    async def get_data(self, filters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Obtém dados do repositório com cache.
        
        Args:
            filters: Filtros para aplicar aos dados
            
        Returns:
            Dados processados e cacheados
        """
        # Implementação com uso de cache
        # ...
```

## 6. Conclusão

A camada de serviços da ViticultureAPI implementa padrões de design que permitem grande flexibilidade e extensibilidade:

1. **Strategy**: Encapsula algoritmos intercambiáveis de processamento de dados
2. **Composite**: Permite combinação de múltiplas estratégias sequencialmente
3. **Transformer**: Facilita transformação progressiva de dados
4. **Repository**: Abstrai acesso a dados permitindo diferentes fontes

Essa arquitetura robusta garante que a aplicação possa lidar com diferentes tipos de dados e processamentos, mantendo o código organizado e facilmente extensível para novos requisitos.