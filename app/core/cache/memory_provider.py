"""
Implementação de cache em memória.

Fornece um provedor de cache que armazena dados na memória do processo.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic
from datetime import datetime, timedelta

from app.core.cache.interface import CacheProvider, TaggedCacheProvider, CacheInfo

logger = logging.getLogger(__name__)

class MemoryCacheProvider(TaggedCacheProvider[str, Any]):
    """
    Implementação de cache em memória com suporte a tags.
    """
    
    def __init__(self, max_size: Optional[int] = None):
        """
        Inicializa o cache em memória.
        
        Args:
            max_size: Tamanho máximo do cache (opcional)
        """
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, int] = {}  # timestamp de expiração
        self._tags: Dict[str, List[str]] = {}  # key -> [tags]
        self._tag_keys: Dict[str, Set[str]] = {}  # tag -> {keys}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave para buscar
            
        Returns:
            Valor associado à chave ou None se não encontrado
        """
        # Verificar se a chave existe e não expirou
        if key in self._cache:
            # Verificar expiração
            if key in self._expiry and self._expiry[key] < int(time.time()):
                # Expirado, remover e retornar None
                await self.delete(key)
                self._misses += 1
                return None
            
            # Chave válida
            self._hits += 1
            return self._cache[key]
        
        # Chave não encontrada
        self._misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Define um valor no cache.
        
        Args:
            key: Chave para armazenar
            value: Valor a ser armazenado
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se o valor foi armazenado com sucesso, False caso contrário
        """
        # Verificar limite de tamanho
        if self._max_size and len(self._cache) >= self._max_size and key not in self._cache:
            # Remover a chave mais antiga (FIFO)
            oldest_key = next(iter(self._cache))
            await self.delete(oldest_key)
        
        # Armazenar valor
        self._cache[key] = value
        
        # Definir expiração se ttl for fornecido
        if ttl is not None:
            self._expiry[key] = int(time.time()) + ttl
        elif key in self._expiry:
            # Remover expiração se ttl for None
            del self._expiry[key]
        
        return True
    
    async def delete(self, key: str) -> bool:
        """
        Remove um valor do cache.
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se o valor foi removido com sucesso, False caso contrário
        """
        if key in self._cache:
            # Remover valor
            del self._cache[key]
            
            # Remover expiração
            if key in self._expiry:
                del self._expiry[key]
            
            # Remover tags
            if key in self._tags:
                # Remover chave de todas as listas de tag_keys
                for tag in self._tags[key]:
                    if tag in self._tag_keys and key in self._tag_keys[tag]:
                        self._tag_keys[tag].remove(key)
                
                # Remover lista de tags da chave
                del self._tags[key]
            
            return True
        
        return False
    
    async def clear(self) -> bool:
        """
        Limpa todo o cache.
        
        Returns:
            True se o cache foi limpo com sucesso, False caso contrário
        """
        self._cache.clear()
        self._expiry.clear()
        self._tags.clear()
        self._tag_keys.clear()
        return True
    
    async def has(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            True se a chave existe, False caso contrário
        """
        # Verificar se a chave existe e não expirou
        if key in self._cache:
            # Verificar expiração
            if key in self._expiry and self._expiry[key] < int(time.time()):
                # Expirado, remover e retornar False
                await self.delete(key)
                return False
            
            # Chave válida
            return True
        
        # Chave não encontrada
        return False
    
    async def ttl(self, key: str) -> Optional[int]:
        """
        Obtém o tempo de vida restante de uma chave.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            Tempo de vida restante em segundos ou None se a chave não existe ou não tem TTL
        """
        if key in self._cache and key in self._expiry:
            ttl = self._expiry[key] - int(time.time())
            return max(0, ttl)
        return None
    
    async def set_with_tags(self, key: str, value: Any, tags: List[str], ttl: Optional[int] = None) -> bool:
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
        # Armazenar valor
        await self.set(key, value, ttl)
        
        # Associar tags
        self._tags[key] = list(set(tags))  # Remover duplicatas
        
        # Atualizar tag_keys
        for tag in self._tags[key]:
            if tag not in self._tag_keys:
                self._tag_keys[tag] = set()
            self._tag_keys[tag].add(key)
        
        return True
    
    async def get_by_tag(self, tag: str) -> Dict[str, Any]:
        """
        Obtém todos os valores associados a uma tag.
        
        Args:
            tag: Tag para buscar
            
        Returns:
            Dicionário de chaves e valores associados à tag
        """
        result = {}
        
        if tag in self._tag_keys:
            # Obter todas as chaves associadas à tag
            for key in list(self._tag_keys[tag]):
                # Verificar se a chave ainda existe e não expirou
                value = await self.get(key)
                if value is not None:
                    result[key] = value
        
        return result
    
    async def invalidate_tag(self, tag: str) -> int:
        """
        Invalida todas as chaves associadas a uma tag.
        
        Args:
            tag: Tag a ser invalidada
            
        Returns:
            Número de chaves invalidadas
        """
        count = 0
        
        if tag in self._tag_keys:
            # Obter todas as chaves associadas à tag
            keys = list(self._tag_keys[tag])
            
            # Remover todas as chaves
            for key in keys:
                if await self.delete(key):
                    count += 1
            
            # Limpar a tag
            self._tag_keys[tag] = set()
        
        return count
    
    async def get_tags(self, key: str) -> List[str]:
        """
        Obtém todas as tags associadas a uma chave.
        
        Args:
            key: Chave para buscar tags
            
        Returns:
            Lista de tags associadas à chave
        """
        return self._tags.get(key, [])
    
    async def get_info(self) -> CacheInfo:
        """
        Obtém informações sobre o cache.
        
        Returns:
            Objeto CacheInfo com informações sobre o cache
        """
        # Verificar e remover chaves expiradas
        now = int(time.time())
        expired_keys = [key for key, exp_time in self._expiry.items() if exp_time < now]
        for key in expired_keys:
            await self.delete(key)
        
        # Coletar estatísticas
        stats = {
            "expired_keys_removed": len(expired_keys),
            "tag_count": len(self._tag_keys),
            "keys_with_ttl": len(self._expiry)
        }
        
        return CacheInfo(
            provider_name="memory",
            item_count=len(self._cache),
            max_size=self._max_size,
            hits=self._hits,
            misses=self._misses,
            tags=list(self._tag_keys.keys()),
            stats=stats
        )
