"""
Fábrica para criar pipelines de dados.

Simplifica a criação de pipelines ETL para os diferentes tipos de dados
da API, reutilizando componentes e configurações comuns.
"""
from typing import Dict, Any, List, Optional, Type, Union, Callable
import pandas as pd
import os

from app.core.pipeline import (
    Pipeline, Extractor, Transformer, Loader, 
    CSVExtractor, JsonExtractor, APIExtractor, WebScrapingExtractor,
    DataFrameToCSVLoader, JsonFileLoader, ModelLoader
)
from app.transform.viticulture import (
    ProductionDataTransformer, ImportExportTransformer, 
    ProcessingTransformer, CommercializationTransformer,
    DataFrameToDictTransformer
)
from app.core.logging import get_logger
import app.core.cache as cache_module  # Import the entire module instead

logger = get_logger(__name__)

# Create a concrete implementation of a cache loader
class ConcreteCacheLoader(Loader[Any]):
    """
    Loader for saving data to cache.
    """
    def __init__(self, key: str, ttl_seconds: int = 3600, tags: Optional[List[str]] = None):
        self.key = key
        self.ttl_seconds = ttl_seconds
        self.tags = tags or []
        self.logger = get_logger(f"loader.cache.{key}")
        
    def load(self, data: Any) -> bool:
        """
        Load data into cache.
        
        Args:
            data: Data to be cached
            
        Returns:
            True if data was successfully cached
        """
        self.logger.info(f"Saving data to cache: {self.key}")
        
        try:
            # Direct access to the global cache dictionary
            from datetime import datetime, timedelta
            
            # Calculate expiry time
            expiry_time = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
            
            # Store in the cache
            cache_module.CACHE[self.key] = (data, expiry_time)
            
            self.logger.info(f"Data successfully cached with TTL: {self.ttl_seconds}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache data: {str(e)}")
            return False

class ETLPipelineFactory:
    """
    Fábrica para criar pipelines ETL para diferentes tipos de dados.
    """
    
    @staticmethod
    def create_csv_to_api_pipeline(
        name: str,
        csv_path: str,
        transformer_class: Type[Transformer],
        ano_filtro: Optional[int] = None,
        pais_filtro: Optional[str] = None,
        source_url: Optional[str] = None,
        cache_key: Optional[str] = None,
        cache_ttl: int = 3600,
        **csv_kwargs
    ) -> Pipeline:
        """
        Cria um pipeline que extrai de CSV e prepara dados para API.
        
        Args:
            name: Nome do pipeline
            csv_path: Caminho para o arquivo CSV
            transformer_class: Classe do transformador a ser usado
            ano_filtro: Ano para filtro (opcional)
            pais_filtro: País para filtro (opcional)
            source_url: URL da fonte dos dados (opcional)
            cache_key: Chave para cachear o resultado (opcional)
            cache_ttl: Tempo de vida do cache em segundos
            **csv_kwargs: Argumentos para o pandas.read_csv
            
        Returns:
            Pipeline configurado
        """
        # Criar o pipeline
        pipeline = Pipeline(name=name)
        
        # Adicionar extrator CSV
        pipeline.add_extractor(CSVExtractor(csv_path, **csv_kwargs))
        
        # Adicionar transformador de dados específico
        transformer_kwargs = {}
        if ano_filtro is not None:
            transformer_kwargs["ano_filtro"] = ano_filtro
        if pais_filtro is not None and transformer_class == ImportExportTransformer:
            transformer_kwargs["pais_filtro"] = pais_filtro
            
        pipeline.add_transformer(transformer_class(**transformer_kwargs))
        
        # Adicionar transformador para o formato de API
        df_to_dict_kwargs = {
            "source": "csv",
            "ano_filtro": ano_filtro,
            "include_source_url": source_url is not None,
            "source_url": source_url
        }
        if pais_filtro is not None:
            df_to_dict_kwargs["pais_filtro"] = pais_filtro
            
        pipeline.add_transformer(DataFrameToDictTransformer(**df_to_dict_kwargs))
        
        # Adicionar cache se necessário
        if cache_key:
            tags = [name]
            if ano_filtro:
                tags.append(f"ano:{ano_filtro}")
            if pais_filtro:
                tags.append(f"pais:{pais_filtro}")
                
            pipeline.add_loader(ConcreteCacheLoader(
                key=cache_key,
                ttl_seconds=cache_ttl,
                tags=tags
            ))
        
        return pipeline
    
    @staticmethod
    def create_scraper_to_api_pipeline(
        name: str,
        scraper_instance: Any,
        scraper_method_name: str,
        ano_filtro: Optional[int] = None,
        pais_filtro: Optional[str] = None,
        cache_key: Optional[str] = None,
        cache_ttl: int = 3600
    ) -> Pipeline:
        """
        Cria um pipeline que usa um scraper existente para obter dados.
        
        Args:
            name: Nome do pipeline
            scraper_instance: Instância do scraper
            scraper_method_name: Nome do método do scraper
            ano_filtro: Ano para filtro (opcional)
            pais_filtro: País para filtro (opcional)
            cache_key: Chave para cachear o resultado (opcional)
            cache_ttl: Tempo de vida do cache em segundos
            
        Returns:
            Pipeline configurado
        """
        # Criar um extrator customizado que usa o scraper
        class ScraperExtractor(Extractor[Dict[str, Any]]):
            def __init__(self, scraper, method_name, **kwargs):
                self.scraper = scraper
                self.method_name = method_name
                self.kwargs = kwargs
                self.logger = get_logger(f"extractor.scraper.{method_name}")
            
            def extract(self) -> Dict[str, Any]:
                self.logger.info(f"Extraindo dados com scraper: {self.method_name}")
                try:
                    method = getattr(self.scraper, self.method_name)
                    data = method(**self.kwargs)
                    self.logger.info(f"Dados extraídos com sucesso")
                    return data
                except Exception as e:
                    self.logger.error(f"Erro ao extrair com scraper: {str(e)}")
                    raise
        
        # Criar o pipeline
        pipeline = Pipeline(name=name)
        
        # Adicionar extrator de scraper
        scraper_kwargs = {}
        if ano_filtro is not None:
            scraper_kwargs["year"] = ano_filtro
        if pais_filtro is not None:
            scraper_kwargs["country"] = pais_filtro
            
        pipeline.add_extractor(ScraperExtractor(
            scraper=scraper_instance,
            method_name=scraper_method_name,
            **scraper_kwargs
        ))
        
        # Adicionar cache se necessário
        if cache_key:
            tags = [name]
            if ano_filtro:
                tags.append(f"ano:{ano_filtro}")
            if pais_filtro:
                tags.append(f"pais:{pais_filtro}")
                
            pipeline.add_loader(ConcreteCacheLoader(
                key=cache_key,
                ttl_seconds=cache_ttl,
                tags=tags
            ))
        
        return pipeline
    
    @staticmethod
    def create_api_to_model_pipeline(
        name: str,
        api_url: str,
        model_class: Type,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Pipeline:
        """
        Cria um pipeline que extrai dados de API e carrega em um modelo.
        
        Args:
            name: Nome do pipeline
            api_url: URL da API
            model_class: Classe do modelo Pydantic
            headers: Cabeçalhos HTTP (opcional)
            params: Parâmetros de query string (opcional)
            
        Returns:
            Pipeline configurado
        """
        # Criar o pipeline
        pipeline = Pipeline(name=name)
        
        # Adicionar extrator de API
        pipeline.add_extractor(APIExtractor(
            url=api_url,
            headers=headers or {},
            params=params or {}
        ))
        
        # Adicionar loader de modelo
        pipeline.add_loader(ModelLoader(model_class=model_class))
        
        return pipeline
