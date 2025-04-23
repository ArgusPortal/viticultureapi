"""
Interfaces para o sistema de cache.

Define contratos para os diferentes tipos de cache na aplicação.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic
from datetime import datetime, timedelta

# Tipo genérico para chaves de cache
K = TypeVar('K')
# Tipo genérico para valores de cache
V = TypeVar('V')

class CacheProvider(Generic[K, V], ABC):
    """
    Interface base para todos os provedores de cache.
    """
    
    @abstractmethod
    async def get(self, key: K) -> Optional[V]:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave para buscar
            
        Returns:
            Valor associado à chave ou None se não encontrado
        """
        pass
    
    @abstractmethod
    async def set(self, key: K, value: V, ttl: Optional[int] = None) -> bool:
        """
        Define um valor no cache.
        
        Args:
            key: Chave para armazenar
            value: Valor a ser armazenado
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se o valor foi armazenado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def delete(self, key: K) -> bool:
        """
        Remove um valor do cache.
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se o valor foi removido com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Limpa todo o cache.
        
        Returns:
            True se o cache foi limpo com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def has(self, key: K) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            True se a chave existe, False caso contrário
        """
        pass
    
    @abstractmethod
    async def ttl(self, key: K) -> Optional[int]:
        """
        Obtém o tempo de vida restante de uma chave.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            Tempo de vida restante em segundos ou None se a chave não existe
        """
        pass
    
    # Adicionando método get_info à interface base
    async def get_info(self) -> 'CacheInfo':
        """
        Obtém informações sobre o cache.
        
        Returns:
            Objeto CacheInfo com informações sobre o cache
        """
        # Implementação padrão básica para provedores que não implementam este método
        return CacheInfo(
            provider_name=self.__class__.__name__,
            item_count=0,
            stats={"info": "Informações detalhadas não disponíveis para este provedor"}
        )

class TaggedCacheProvider(CacheProvider[K, V], ABC):
    """
    Interface para provedores de cache com suporte a tags.
    """
    
    @abstractmethod
    async def set_with_tags(self, key: K, value: V, tags: List[str], ttl: Optional[int] = None) -> bool:
        """
        Define um valor no cache com tags associadas.
        
        Args:
            key: Chave para armazenar
            value: Valor a ser armazenado
            tags: Lista de tags a serem associadas à chave
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se o valor foi armazenado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def get_by_tag(self, tag: str) -> Dict[K, V]:
        """
        Obtém todos os valores associados a uma tag.
        
        Args:
            tag: Tag para buscar
            
        Returns:
            Dicionário de chaves e valores associados à tag
        """
        pass
    
    @abstractmethod
    async def invalidate_tag(self, tag: str) -> int:
        """
        Invalida todas as chaves associadas a uma tag.
        
        Args:
            tag: Tag a ser invalidada
            
        Returns:
            Número de chaves invalidadas
        """
        pass
    
    @abstractmethod
    async def get_tags(self, key: K) -> List[str]:
        """
        Obtém todas as tags associadas a uma chave.
        
        Args:
            key: Chave para buscar tags
            
        Returns:
            Lista de tags associadas à chave
        """
        pass

class CacheInfo:
    """Classe para armazenar informações sobre o cache."""
    
    def __init__(self, 
                 provider_name: str,
                 item_count: int,
                 max_size: Optional[int] = None,
                 hits: int = 0,
                 misses: int = 0,
                 tags: Optional[List[str]] = None,
                 stats: Optional[Dict[str, Any]] = None):
        self.provider_name = provider_name
        self.item_count = item_count
        self.max_size = max_size
        self.hits = hits
        self.misses = misses
        self.tags = tags or []
        self.stats = stats or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte as informações do cache para um dicionário."""
        return {
            "provider": self.provider_name,
            "items": self.item_count,
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": (self.hits / (self.hits + self.misses)) if (self.hits + self.misses) > 0 else 0,
            "tags": self.tags,
            "stats": self.stats
        }
