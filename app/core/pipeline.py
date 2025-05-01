"""
Pipeline de dados ETL (Extract, Transform, Load).

Define interfaces e implementações para processamento de dados
em pipeline, permitindo encadear operações de extração,
transformação e carregamento de forma flexível.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generic, TypeVar, Callable, Optional, Union, Iterator, Iterable
import logging
from datetime import datetime
import pandas as pd
import numpy as np
from pydantic import BaseModel

from app.core.logging import get_logger

# Tipos genéricos para os dados
T = TypeVar('T')  # Tipo de entrada
U = TypeVar('U')  # Tipo de saída
D = TypeVar('D')  # Tipo de dados (para DataFrames ou dicionários)

logger = get_logger(__name__)

# ----- INTERFACES BASE DO PIPELINE -----

class Extractor(Generic[T], ABC):
    """
    Interface para extrair dados de uma fonte.
    
    Responsável por obter dados brutos de uma fonte externa
    (arquivo, API, banco de dados, etc.) e fornecê-los para
    a próxima etapa do pipeline.
    """
    
    @abstractmethod
    def extract(self) -> T:
        """
        Extrai dados da fonte.
        
        Returns:
            Dados extraídos
        """
        pass

class Transformer(Generic[T, U], ABC):
    """
    Interface para transformar dados de um tipo para outro.
    
    Responsável por processar e transformar dados de um formato
    para outro, realizando limpeza, filtragem, agregação, etc.
    """
    
    @abstractmethod
    def transform(self, data: T) -> U:
        """
        Transforma os dados.
        
        Args:
            data: Dados de entrada
            
        Returns:
            Dados transformados
        """
        pass

class Loader(Generic[T], ABC):
    """
    Interface para carregar dados em um destino.
    
    Responsável por persistir os dados transformados em um destino
    (banco de dados, arquivo, cache, etc.).
    """
    
    @abstractmethod
    def load(self, data: T) -> Any:
        """
        Carrega os dados no destino.
        
        Args:
            data: Dados a serem carregados
            
        Returns:
            Resultado do carregamento (opcional)
        """
        pass

# ----- IMPLEMENTAÇÃO DO PIPELINE -----

class Pipeline:
    """
    Pipeline de processamento de dados ETL.
    
    Encadeia operações de extração, transformação e carregamento
    de dados, permitindo construir fluxos de processamento flexíveis.
    """
    
    def __init__(self, name: str = "pipeline"):
        """
        Inicializa o pipeline.
        
        Args:
            name: Nome do pipeline para identificação em logs
        """
        self.name = name
        self.steps: List[Callable] = []
        self.extractors: List[Extractor] = []
        self.transformers: List[Transformer] = []
        self.loaders: List[Loader] = []
        self.logger = get_logger(f"pipeline.{name}")
    
    def add_extractor(self, extractor: Extractor) -> 'Pipeline':
        """
        Adiciona um extrator ao pipeline.
        
        Args:
            extractor: Extrator a ser adicionado
            
        Returns:
            Pipeline atualizado para encadeamento de métodos
        """
        self.extractors.append(extractor)
        self.steps.append(extractor.extract)
        return self
    
    def add_transformer(self, transformer: Transformer) -> 'Pipeline':
        """
        Adiciona um transformador ao pipeline.
        
        Args:
            transformer: Transformador a ser adicionado
            
        Returns:
            Pipeline atualizado para encadeamento de métodos
        """
        self.transformers.append(transformer)
        self.steps.append(transformer.transform)
        return self
    
    def add_loader(self, loader: Loader) -> 'Pipeline':
        """
        Adiciona um carregador ao pipeline.
        
        Args:
            loader: Carregador a ser adicionado
            
        Returns:
            Pipeline atualizado para encadeamento de métodos
        """
        self.loaders.append(loader)
        self.steps.append(loader.load)
        return self
    
    def add_step(self, step: Callable[[Any], Any], name: Optional[str] = None) -> 'Pipeline':
        """
        Adiciona um passo genérico ao pipeline.
        
        Args:
            step: Função que processa os dados
            name: Nome opcional do passo para logging
            
        Returns:
            Pipeline atualizado para encadeamento de métodos
        """
        if name:
            # Criamos um wrapper para poder fazer log com o nome do passo
            original_step = step
            
            def named_step(data: Any) -> Any:
                self.logger.info(f"Executando passo '{name}'")
                start_time = datetime.now()
                result = original_step(data)
                duration = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"Passo '{name}' concluído em {duration:.2f}s")
                return result
            
            self.steps.append(named_step)
        else:
            self.steps.append(step)
        
        return self
    
    def execute(self) -> Any:
        """
        Executa o pipeline completo.
        
        Returns:
            Resultado da execução do pipeline
        """
        if not self.steps:
            self.logger.warning("Pipeline vazio, nada a executar")
            return None
        
        self.logger.info(f"Iniciando execução do pipeline '{self.name}' com {len(self.steps)} passos")
        start_time = datetime.now()
        
        # Inicia com o primeiro passo
        data = self.steps[0]()
        
        # Executa os passos seguintes
        for i, step in enumerate(self.steps[1:], 1):
            try:
                self.logger.debug(f"Executando passo {i}")
                data = step(data)
            except Exception as e:
                self.logger.error(f"Erro no passo {i}: {str(e)}")
                raise
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Pipeline '{self.name}' concluído em {duration:.2f}s")
        
        return data

# ----- TRANSFORMADORES GENÉRICOS -----

class DataFrameTransformer(Transformer[pd.DataFrame, pd.DataFrame]):
    """
    Transformador base para operações com DataFrame.
    
    Fornece métodos utilitários para transformações comuns em DataFrames.
    """
    
    def __init__(self, name: str = "dataframe_transformer"):
        """
        Inicializa o transformador.
        
        Args:
            name: Nome do transformador para logs
        """
        self.name = name
        self.logger = get_logger(f"transformer.{name}")
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma o DataFrame (método a ser sobrescrito).
        
        Args:
            data: DataFrame de entrada
            
        Returns:
            DataFrame transformado
        """
        return data
    
    def rename_columns(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Renomeia colunas do DataFrame.
        
        Args:
            df: DataFrame
            mapping: Mapeamento {nome_antigo: nome_novo}
            
        Returns:
            DataFrame com colunas renomeadas
        """
        return df.rename(columns=mapping)
    
    def filter_rows(self, df: pd.DataFrame, condition: Callable[[pd.Series], bool]) -> pd.DataFrame:
        """
        Filtra linhas do DataFrame.
        
        Args:
            df: DataFrame
            condition: Função que recebe uma linha e retorna True/False
            
        Returns:
            DataFrame filtrado
        """
        return df[df.apply(condition, axis=1)]
    
    def select_columns(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Seleciona colunas do DataFrame.
        
        Args:
            df: DataFrame
            columns: Lista de colunas a manter
            
        Returns:
            DataFrame com as colunas selecionadas
        """
        return df[columns]
    
    def apply_function(self, df: pd.DataFrame, func: Callable, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Aplica uma função às colunas especificadas.
        
        Args:
            df: DataFrame
            func: Função a aplicar
            columns: Colunas onde aplicar (None = todas)
            
        Returns:
            DataFrame transformado
        """
        result = df.copy()
        if columns:
            for col in columns:
                if col in result.columns:
                    result[col] = result[col].apply(func)
        else:
            result = result.apply(func)
        return result
    
    def fill_na(self, df: pd.DataFrame, value: Any = 0, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Preenche valores NA/NaN.
        
        Args:
            df: DataFrame
            value: Valor para preencher
            columns: Colunas onde aplicar (None = todas)
            
        Returns:
            DataFrame sem valores NA
        """
        if columns:
            result = df.copy()
            for col in columns:
                if col in result.columns:
                    result[col] = result[col].fillna(value)
            return result
        else:
            return df.fillna(value)
    
    def drop_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove linhas duplicadas.
        
        Args:
            df: DataFrame
            subset: Colunas a considerar (None = todas)
            
        Returns:
            DataFrame sem duplicatas
        """
        return df.drop_duplicates(subset=subset)

class DictTransformer(Transformer[Dict[str, Any], Dict[str, Any]]):
    """
    Transformador base para operações com dicionários.
    
    Fornece métodos utilitários para transformações comuns em dicionários.
    """
    
    def __init__(self, name: str = "dict_transformer"):
        """
        Inicializa o transformador.
        
        Args:
            name: Nome do transformador para logs
        """
        self.name = name
        self.logger = get_logger(f"transformer.{name}")
    
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma o dicionário (método a ser sobrescrito).
        
        Args:
            data: Dicionário de entrada
            
        Returns:
            Dicionário transformado
        """
        return data
    
    def rename_keys(self, data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Renomeia chaves do dicionário.
        
        Args:
            data: Dicionário
            mapping: Mapeamento {chave_antiga: chave_nova}
            
        Returns:
            Dicionário com chaves renomeadas
        """
        result = {}
        for key, value in data.items():
            new_key = mapping.get(key, key)
            result[new_key] = value
        return result
    
    def filter_keys(self, data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """
        Filtra chaves do dicionário.
        
        Args:
            data: Dicionário
            keys: Chaves a manter
            
        Returns:
            Dicionário apenas com as chaves especificadas
        """
        return {k: v for k, v in data.items() if k in keys}
    
    def apply_function(self, data: Dict[str, Any], func: Callable, keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Aplica uma função aos valores do dicionário.
        
        Args:
            data: Dicionário
            func: Função a aplicar
            keys: Chaves onde aplicar (None = todas)
            
        Returns:
            Dicionário transformado
        """
        result = data.copy()
        if keys:
            for key in keys:
                if key in result:
                    result[key] = func(result[key])
        else:
            result = {k: func(v) for k, v in result.items()}
        return result

# ----- IMPLEMENTAÇÕES DE EXTRATORES -----

class CSVExtractor(Extractor[pd.DataFrame]):
    """
    Extrai dados de um arquivo CSV.
    """
    
    def __init__(self, file_path: str, **read_csv_kwargs):
        """
        Inicializa o extrator.
        
        Args:
            file_path: Caminho para o arquivo CSV
            **read_csv_kwargs: Argumentos para pandas.read_csv
        """
        self.file_path = file_path
        self.read_csv_kwargs = read_csv_kwargs
        self.logger = get_logger(f"extractor.csv.{file_path}")
    
    def extract(self) -> pd.DataFrame:
        """
        Extrai dados do arquivo CSV.
        
        Returns:
            DataFrame com os dados do CSV
        """
        self.logger.info(f"Extraindo dados do arquivo CSV: {self.file_path}")
        try:
            df = pd.read_csv(self.file_path, **self.read_csv_kwargs)
            self.logger.info(f"Dados extraídos com sucesso: {len(df)} linhas, {len(df.columns)} colunas")
            return df
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados do CSV: {str(e)}")
            raise

class JsonExtractor(Extractor[Dict[str, Any]]):
    """
    Extrai dados de um arquivo JSON.
    """
    
    def __init__(self, file_path: str, **read_json_kwargs):
        """
        Inicializa o extrator.
        
        Args:
            file_path: Caminho para o arquivo JSON
            **read_json_kwargs: Argumentos para pandas.read_json
        """
        self.file_path = file_path
        self.read_json_kwargs = read_json_kwargs
        self.logger = get_logger(f"extractor.json.{file_path}")
    
    def extract(self) -> Dict[str, Any]:
        """
        Extrai dados do arquivo JSON.
        
        Returns:
            Dicionário com os dados do JSON
        """
        self.logger.info(f"Extraindo dados do arquivo JSON: {self.file_path}")
        try:
            import json
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"Dados extraídos com sucesso")
            return data
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados do JSON: {str(e)}")
            raise

class APIExtractor(Extractor[Dict[str, Any]]):
    """
    Extrai dados de uma API REST.
    """
    
    def __init__(self, url: str, method: str = "GET", 
                 headers: Optional[Dict[str, str]] = None, 
                 params: Optional[Dict[str, Any]] = None, 
                 json_body: Optional[Dict[str, Any]] = None):
        """
        Inicializa o extrator.
        
        Args:
            url: URL da API
            method: Método HTTP (GET, POST, etc.)
            headers: Cabeçalhos HTTP (opcional)
            params: Parâmetros de query string (opcional)
            json_body: Corpo da requisição em JSON (para POST, PUT, etc.) (opcional)
        """
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.params = params or {}
        self.json_body = json_body
        self.logger = get_logger(f"extractor.api.{url}")
    
    def extract(self) -> Dict[str, Any]:
        """
        Extrai dados da API.
        
        Returns:
            Dados retornados pela API
        """
        import requests
        
        self.logger.info(f"Extraindo dados da API: {self.url} ({self.method})")
        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                params=self.params,
                json=self.json_body
            )
            response.raise_for_status()  # Raise exception for 4xx/5xx responses
            data = response.json()
            self.logger.info(f"Dados extraídos com sucesso: status {response.status_code}")
            return data
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados da API: {str(e)}")
            raise

class WebScrapingExtractor(Extractor[Dict[str, Any]]):
    """
    Extrai dados de páginas web via web scraping.
    """
    
    def __init__(self, url: str, scraping_function: Callable[[str], Dict[str, Any]]):
        """
        Inicializa o extrator.
        
        Args:
            url: URL da página
            scraping_function: Função que recebe o HTML e retorna os dados extraídos
        """
        self.url = url
        self.scraping_function = scraping_function
        self.logger = get_logger(f"extractor.scraping.{url}")
    
    def extract(self) -> Dict[str, Any]:
        """
        Extrai dados via web scraping.
        
        Returns:
            Dados extraídos da página
        """
        import requests
        from bs4 import BeautifulSoup
        
        self.logger.info(f"Extraindo dados via web scraping: {self.url}")
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            html = response.text
            data = self.scraping_function(html)
            self.logger.info(f"Dados extraídos com sucesso")
            return data
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados via web scraping: {str(e)}")
            raise

# ----- IMPLEMENTAÇÕES DE LOADERS -----

class DataFrameToCSVLoader(Loader[pd.DataFrame]):
    """
    Carrega um DataFrame em um arquivo CSV.
    """
    
    def __init__(self, file_path: str, **to_csv_kwargs):
        """
        Inicializa o loader.
        
        Args:
            file_path: Caminho para o arquivo CSV
            **to_csv_kwargs: Argumentos para DataFrame.to_csv
        """
        self.file_path = file_path
        self.to_csv_kwargs = to_csv_kwargs
        self.logger = get_logger(f"loader.csv.{file_path}")
    
    def load(self, data: pd.DataFrame) -> str:
        """
        Carrega o DataFrame em um arquivo CSV.
        
        Args:
            data: DataFrame a ser salvo
            
        Returns:
            Caminho do arquivo salvo
        """
        self.logger.info(f"Salvando DataFrame em CSV: {self.file_path}")
        try:
            data.to_csv(self.file_path, **self.to_csv_kwargs)
            self.logger.info(f"Dados salvos com sucesso: {len(data)} linhas")
            return self.file_path
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {str(e)}")
            raise

class JsonFileLoader(Loader[Dict[str, Any]]):
    """
    Carrega um dicionário em um arquivo JSON.
    """
    
    def __init__(self, file_path: str, indent: int = 2):
        """
        Inicializa o loader.
        
        Args:
            file_path: Caminho para o arquivo JSON
            indent: Indentação do JSON
        """
        self.file_path = file_path
        self.indent = indent
        self.logger = get_logger(f"loader.json.{file_path}")
    
    def load(self, data: Dict[str, Any]) -> str:
        """
        Carrega o dicionário em um arquivo JSON.
        
        Args:
            data: Dicionário a ser salvo
            
        Returns:
            Caminho do arquivo salvo
        """
        self.logger.info(f"Salvando dados em JSON: {self.file_path}")
        try:
            import json
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=self.indent)
            self.logger.info(f"Dados salvos com sucesso")
            return self.file_path
        except Exception as e:
            self.logger.error(f"Erro ao salvar JSON: {str(e)}")
            raise

class CacheLoader(Loader[Any]):
    """
    Carrega dados no sistema de cache.
    """
    
    # Class-level cache dictionary as a fallback
    _local_cache = {}
    
    def __init__(self, key: str, ttl_seconds: int = 3600, tags: Optional[List[str]] = None):
        """
        Inicializa o loader.
        
        Args:
            key: Chave para o cache
            ttl_seconds: Tempo de vida em segundos
            tags: Tags para categorizar o cache (opcional)
        """
        self.key = key
        self.ttl_seconds = ttl_seconds
        self.tags = tags or []
        self.logger = get_logger(f"loader.cache.{key}")
    
    def load(self, data: Any) -> bool:
        """
        Carrega os dados no cache.
        
        Args:
            data: Dados a serem cacheados
            
        Returns:
            True se os dados foram cacheados com sucesso
        """
        self.logger.info(f"Salvando dados no cache: {self.key}")
        
        # Estratégia 1: Usar a função cache_result como função decoradora
        try:
            # Importar apenas o que é utilizado do módulo de cache
            from app.core.cache import cache_result
            from datetime import datetime, timedelta
            
            # Criar e executar uma função assíncrona temporária para guardar os dados
            @cache_result(ttl_seconds=self.ttl_seconds)
            async def _cache_data():
                """Função temporária apenas para armazenar os dados no cache"""
                return data
                
            # Executar a função assíncrona para cachear os dados
            import asyncio
            try:
                # Para Python 3.7+
                asyncio.run(_cache_data())
                self.logger.info(f"Dados cacheados com sucesso via cache_result: TTL={self.ttl_seconds}s")
                return True
            except (RuntimeError, ValueError) as e:
                # Se já estiver em um loop de eventos ou outra exceção
                self.logger.debug(f"Não foi possível usar asyncio.run: {str(e)}")
                
                # Tentativa alternativa usando create_task em um loop existente
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Se já estiver em um loop, criar uma tarefa
                    asyncio.create_task(_cache_data())
                    self.logger.info(f"Dados enviados para cache via create_task: TTL={self.ttl_seconds}s")
                    return True
                else:
                    # Se não estiver em um loop, mas run() falhou
                    loop.run_until_complete(_cache_data())
                    self.logger.info(f"Dados cacheados com sucesso via run_until_complete: TTL={self.ttl_seconds}s")
                    return True
                    
        except ImportError as e:
            self.logger.warning(f"Módulo de cache não disponível: {str(e)}")
            
        except Exception as e:
            self.logger.warning(f"Erro ao usar cache_result: {str(e)}")
        
        # Estratégia 2: Fallback para cache local
        try:
            from datetime import datetime, timedelta
            expiry_time = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
            
            # Usar cache local da classe
            key_with_tags = self.key
            if self.tags:
                key_with_tags = f"{self.key}:{','.join(self.tags)}"
                
            self._local_cache[key_with_tags] = (data, expiry_time)
            self.logger.info(f"Dados cacheados com sucesso no cache local: TTL={self.ttl_seconds}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear dados: {str(e)}")
            return False

class ModelLoader(Loader[Dict[str, Any]]):
    """
    Carrega dados em um modelo Pydantic.
    """
    
    def __init__(self, model_class: type):
        """
        Inicializa o loader.
        
        Args:
            model_class: Classe do modelo Pydantic
        """
        self.model_class = model_class
        self.logger = get_logger(f"loader.model.{model_class.__name__}")
    
    def load(self, data: Dict[str, Any]) -> BaseModel:
        """
        Carrega os dados no modelo.
        
        Args:
            data: Dados a serem carregados
            
        Returns:
            Instância do modelo
        """
        self.logger.info(f"Carregando dados no modelo {self.model_class.__name__}")
        try:
            model = self.model_class(**data)
            self.logger.info(f"Dados carregados com sucesso no modelo")
            return model
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados no modelo: {str(e)}")
            raise
