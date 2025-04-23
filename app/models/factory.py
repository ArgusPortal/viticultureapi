"""
Fábricas para converter dados brutos em modelos de domínio.

Implementa o padrão Factory para criar instâncias de modelos a partir de dados brutos.
"""
import logging
from typing import List, Dict, Any, Type, TypeVar, Generic, Optional, Union, cast
from pydantic import BaseModel

from app.models.base import DataResponse
from app.models.production import (
    ProductionRecord, WineProductionRecord, JuiceProductionRecord, 
    DerivativeProductionRecord, ProductionResponse, WineProductionResponse,
    JuiceProductionResponse, DerivativeProductionResponse
)
from app.models.trade import (
    TradeRecord, ImportRecord, ExportRecord,
    TradeResponse, ImportResponse, ExportResponse
)
from app.models.commercialization import CommercializationRecord, CommercializationResponse
from app.models.processing import ProcessingRecord, DetailedProcessingRecord, ProcessingResponse, DetailedProcessingResponse
from app.utils.data_cleaner import clean_navigation_arrows

logger = logging.getLogger(__name__)

# Definir tipo genérico T para ser usado nas interfaces
T = TypeVar('T', bound=BaseModel)
R = TypeVar('R', bound=DataResponse)

class ModelFactory(Generic[T]):
    """Fábrica base para criar modelos a partir de dados brutos."""
    
    def __init__(self, model_class: Type[T]):
        """
        Inicializa a fábrica com a classe do modelo.
        
        Args:
            model_class: Classe do modelo a ser criado
        """
        self.model_class = model_class
    
    def create_from_dict(self, data: Dict[str, Any]) -> T:
        """
        Cria uma instância do modelo a partir de um dicionário.
        
        Args:
            data: Dicionário com os dados
            
        Returns:
            Instância do modelo
        """
        try:
            return self.model_class(**data)
        except Exception as e:
            logger.error(f"Erro ao criar modelo {self.model_class.__name__}: {str(e)}")
            logger.debug(f"Dados: {data}")
            
            # Tentar criar com dados vazios como fallback
            if hasattr(self.model_class, "__fields__"):
                empty_data = {field: None for field in self.model_class.__fields__}
                try:
                    return self.model_class(**empty_data)
                except Exception:
                    pass
            
            # Se tudo falhar, reraise a exceção original
            raise
    
    def create_from_list(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Cria uma lista de instâncias do modelo a partir de uma lista de dicionários.
        
        Args:
            data_list: Lista de dicionários com os dados
            
        Returns:
            Lista de instâncias do modelo
        """
        # Limpar dados de navegação antes de converter
        cleaned_data = clean_navigation_arrows(data_list)
        
        result = []
        for item in cleaned_data:
            try:
                model = self.create_from_dict(item)
                result.append(model)
            except Exception as e:
                logger.error(f"Erro ao processar item: {str(e)}")
                logger.debug(f"Item com erro: {item}")
                # Continuar processando os próximos itens
        
        return result

class ResponseFactory:
    """Fábrica para criar respostas da API a partir de dados brutos."""
    
    @staticmethod
    def create_response(
        data_list: List[Dict[str, Any]], 
        response_class: Type[R], 
        record_class: Type[BaseModel],
        source: str,
        **kwargs
    ) -> R:
        """
        Cria uma resposta da API a partir de uma lista de dicionários.
        
        Args:
            data_list: Lista de dicionários com os dados
            response_class: Classe da resposta
            record_class: Classe do modelo de registro
            source: Fonte dos dados
            **kwargs: Parâmetros adicionais para a resposta
            
        Returns:
            Instância da resposta
        """
        factory = ModelFactory(record_class)
        records = factory.create_from_list(data_list)
        
        # Criar a instância e usar cast para garantir o tipo correto
        return response_class(
            data=records,
            count=len(records),
            source=source,
            **kwargs
        )
    
    @staticmethod
    def create_production_response(
        data: Dict[str, Any], 
        year: Optional[int] = None
    ) -> ProductionResponse:
        """
        Cria uma resposta de produção a partir de dados brutos.
        
        Args:
            data: Dicionário com os dados brutos e metadados
            year: Ano para filtro, se aplicável
            
        Returns:
            Instância de ProductionResponse
        """
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=ProductionResponse,
            record_class=ProductionRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year
        )
        return cast(ProductionResponse, response)
    
    @staticmethod
    def create_wine_production_response(
        data: Dict[str, Any], 
        year: Optional[int] = None
    ) -> WineProductionResponse:
        """Cria uma resposta de produção de vinhos."""
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=WineProductionResponse,
            record_class=WineProductionRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year
        )
        return cast(WineProductionResponse, response)
    
    @staticmethod
    def create_juice_production_response(
        data: Dict[str, Any], 
        year: Optional[int] = None
    ) -> JuiceProductionResponse:
        """Cria uma resposta de produção de sucos."""
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=JuiceProductionResponse,
            record_class=JuiceProductionRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year
        )
        return cast(JuiceProductionResponse, response)
    
    @staticmethod
    def create_derivative_production_response(
        data: Dict[str, Any], 
        year: Optional[int] = None
    ) -> DerivativeProductionResponse:
        """Cria uma resposta de produção de derivados."""
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=DerivativeProductionResponse,
            record_class=DerivativeProductionRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year
        )
        return cast(DerivativeProductionResponse, response)
    
    @staticmethod
    def create_import_response(
        data: Dict[str, Any], 
        year: Optional[int] = None,
        country: Optional[str] = None
    ) -> ImportResponse:
        """Cria uma resposta de importação."""
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=ImportResponse,
            record_class=ImportRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year,
            pais_filtro=country
        )
        return cast(ImportResponse, response)
    
    @staticmethod
    def create_export_response(
        data: Dict[str, Any], 
        year: Optional[int] = None,
        country: Optional[str] = None
    ) -> ExportResponse:
        """Cria uma resposta de exportação."""
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=ExportResponse,
            record_class=ExportRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year,
            pais_filtro=country
        )
        return cast(ExportResponse, response)
    
    @staticmethod
    def create_commercialization_response(
        data: Dict[str, Any], 
        year: Optional[int] = None
    ) -> CommercializationResponse:
        """Cria uma resposta de comercialização."""
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=CommercializationResponse,
            record_class=CommercializationRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year
        )
        return cast(CommercializationResponse, response)
    
    @staticmethod
    def create_processing_response(
        data: Dict[str, Any], 
        year: Optional[int] = None
    ) -> ProcessingResponse:
        """Cria uma resposta de processamento."""
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=ProcessingResponse,
            record_class=ProcessingRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year
        )
        return cast(ProcessingResponse, response)
    
    @staticmethod
    def create_detailed_processing_response(
        data: Dict[str, Any], 
        year: Optional[int] = None
    ) -> DetailedProcessingResponse:
        """Cria uma resposta de processamento detalhado."""
        response = ResponseFactory.create_response(
            data_list=data.get("data", []),
            response_class=DetailedProcessingResponse,
            record_class=DetailedProcessingRecord,
            source=data.get("source", "unknown"),
            ano_filtro=year
        )
        return cast(DetailedProcessingResponse, response)
