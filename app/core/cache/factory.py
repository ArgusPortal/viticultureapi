"""
Factory para providers de cache.

Fornece uma interface para criar e gerenciar diferentes providers de cache.
"""
import logging
from typing import Dict, Optional, Type, Any, List, Union, cast

from app.core.cache.interface import CacheProvider, TaggedCacheProvider, CacheInfo
from app.core.cache.memory_provider import MemoryCacheProvider
from app.core.cache.file_provider import FileCacheProvider

logger = logging.getLogger(__name__)

class CacheFactory:
    """
    Factory para criação e gerenciamento de providers de cache.
    """
    
    _instance = None
    _providers: Dict[str, CacheProvider] = {}
    _default_provider: str = "memory"
    
    @classmethod
    def get_instance(cls) -> 'CacheFactory':
        """
        Obtém a instância singleton da factory.
        
        Returns:
            Instância da factory
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa a factory."""
        # Registrar providers padrão
        self._register_default_providers()
    
    def _register_default_providers(self) -> None:
        """Registra os providers padrão."""
        # Provider de memória
        self.register_provider("memory", MemoryCacheProvider())
        
        # Provider de arquivo
        self.register_provider("file", FileCacheProvider())
    
    def register_provider(self, name: str, provider: CacheProvider) -> None:
        """
        Registra um provider de cache.
        
        Args:
            name: Nome do provider
            provider: Instância do provider
        """
        if name in self._providers:
            logger.warning(f"Provider '{name}' already registered. Overwriting.")
        
        self._providers[name] = provider
        logger.info(f"Registered cache provider: {name}")
    
    def get_provider(self, name: Optional[str] = None) -> CacheProvider:
        """
        Obtém um provider de cache.
        
        Args:
            name: Nome do provider ou None para usar o padrão
            
        Returns:
            Instância do provider
            
        Raises:
            ValueError: Se o provider não estiver registrado
        """
        provider_name = name or self._default_provider
        
        if provider_name not in self._providers:
            raise ValueError(f"Cache provider '{provider_name}' not registered")
        
        return self._providers[provider_name]
    
    def set_default_provider(self, name: str) -> None:
        """
        Define o provider padrão.
        
        Args:
            name: Nome do provider
            
        Raises:
            ValueError: Se o provider não estiver registrado
        """
        if name not in self._providers:
            raise ValueError(f"Cache provider '{name}' not registered")
        
        self._default_provider = name
        logger.info(f"Default cache provider set to '{name}'")
    
    def get_available_providers(self) -> List[str]:
        """
        Obtém a lista de providers disponíveis.
        
        Returns:
            Lista de nomes de providers
        """
        return list(self._providers.keys())
    
    async def get_providers_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtém informações sobre todos os providers.
        
        Returns:
            Dicionário com informações sobre cada provider
        """
        result = {}
        
        for name, provider in self._providers.items():
            try:
                # Como o método get_info() agora é parte da interface CacheProvider,
                # podemos chamá-lo diretamente sem verificar sua existência
                info = await provider.get_info()
                result[name] = info.to_dict()
            except Exception as e:
                logger.error(f"Erro ao obter informações do provider '{name}': {str(e)}")
                result[name] = {"provider": name, "error": str(e)}
        
        return result
