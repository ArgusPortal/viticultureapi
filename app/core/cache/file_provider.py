"""
Implementação de cache baseado em arquivo.

Fornece um provedor de cache que persiste dados em arquivos.
"""
import os
import json
import logging
import pickle
import tempfile
import time
import shutil
from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic
from pathlib import Path

from app.core.cache.interface import CacheProvider, TaggedCacheProvider, CacheInfo

logger = logging.getLogger(__name__)

class FileCacheProvider(TaggedCacheProvider[str, Any]):
    """
    Implementação de cache baseado em arquivo com suporte a tags.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, use_pickle: bool = True):
        """
        Inicializa o cache baseado em arquivo.
        
        Args:
            cache_dir: Diretório para armazenar os arquivos de cache (opcional)
            use_pickle: Se True, usa pickle para serialização; se False, usa JSON
        """
        self._cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "viticultureapi_cache")
        self._use_pickle = use_pickle
        self._meta_file = os.path.join(self._cache_dir, "meta.json")
        self._hits = 0
        self._misses = 0
        
        # Criar diretório de cache se não existir
        os.makedirs(self._cache_dir, exist_ok=True)
        
        # Inicializar metadados
        self._metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """
        Carrega os metadados do cache.
        
        Returns:
            Dicionário com metadados
        """
        if os.path.exists(self._meta_file):
            try:
                with open(self._meta_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Erro ao carregar metadados do cache: {str(e)}")
        
        # Inicializar metadados vazios
        return {
            "keys": {},      # key -> {expiry, filename, tags}
            "tags": {},      # tag -> [keys]
            "stats": {
                "hits": 0,
                "misses": 0
            }
        }
    
    def _save_metadata(self) -> None:
        """Salva os metadados do cache."""
        try:
            # Usar arquivo temporário para evitar corrupção em caso de falha
            temp_file = f"{self._meta_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
            
            # Substituir arquivo original pelo temporário
            shutil.move(temp_file, self._meta_file)
        except IOError as e:
            logger.error(f"Erro ao salvar metadados do cache: {str(e)}")
    
    def _get_file_path(self, key: str) -> str:
        """
        Obtém o caminho do arquivo de cache para uma chave.
        
        Args:
            key: Chave do cache
            
        Returns:
            Caminho do arquivo
        """
        # Verificar se já existe um arquivo associado à chave
        if key in self._metadata["keys"] and "filename" in self._metadata["keys"][key]:
            return os.path.join(self._cache_dir, self._metadata["keys"][key]["filename"])
        
        # Criar nome de arquivo baseado na chave (sanitizado)
        safe_key = ''.join(c if c.isalnum() else '_' for c in key)
        filename = f"{safe_key}_{hash(key) % 1000000}.cache"
        return os.path.join(self._cache_dir, filename)
    
    def _is_expired(self, key: str) -> bool:
        """
        Verifica se uma chave expirou.
        
        Args:
            key: Chave para verificar
            
        Returns:
            True se a chave expirou, False caso contrário
        """
        if key in self._metadata["keys"] and "expiry" in self._metadata["keys"][key]:
            expiry = self._metadata["keys"][key]["expiry"]
            return expiry is not None and expiry < int(time.time())
        return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave para buscar
            
        Returns:
            Valor associado à chave ou None se não encontrado
        """
        # Verificar se a chave existe nos metadados
        if key not in self._metadata["keys"]:
            self._misses += 1
            self._metadata["stats"]["misses"] += 1
            self._save_metadata()
            return None
        
        # Verificar se a chave expirou
        if self._is_expired(key):
            # Expirado, remover e retornar None
            await self.delete(key)
            self._misses += 1
            self._metadata["stats"]["misses"] += 1
            self._save_metadata()
            return None
        
        # Obter caminho do arquivo
        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            # Arquivo não encontrado, remover chave dos metadados
            await self.delete(key)
            self._misses += 1
            self._metadata["stats"]["misses"] += 1
            self._save_metadata()
            return None
        
        try:
            # Carregar valor do arquivo
            if self._use_pickle:
                with open(file_path, 'rb') as f:
                    value = pickle.load(f)
            else:
                with open(file_path, 'r') as f:
                    value = json.load(f)
            
            self._hits += 1
            self._metadata["stats"]["hits"] += 1
            self._save_metadata()
            return value
        except (pickle.PickleError, json.JSONDecodeError, IOError) as e:
            logger.error(f"Erro ao carregar valor do cache: {str(e)}")
            self._misses += 1
            self._metadata["stats"]["misses"] += 1
            self._save_metadata()
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
        # Obter caminho do arquivo
        file_path = self._get_file_path(key)
        filename = os.path.basename(file_path)
        
        try:
            # Salvar valor no arquivo
            if self._use_pickle:
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                with open(file_path, 'w') as f:
                    json.dump(value, f, indent=2)
            
            # Atualizar metadados
            if key not in self._metadata["keys"]:
                self._metadata["keys"][key] = {}
            
            self._metadata["keys"][key]["filename"] = filename
            
            # Definir expiração se ttl for fornecido
            if ttl is not None:
                self._metadata["keys"][key]["expiry"] = int(time.time()) + ttl
            elif "expiry" in self._metadata["keys"][key]:
                # Remover expiração se ttl for None
                del self._metadata["keys"][key]["expiry"]
            
            # Preservar tags existentes
            if "tags" not in self._metadata["keys"][key]:
                self._metadata["keys"][key]["tags"] = []
            
            self._save_metadata()
            return True
        except (pickle.PickleError, IOError) as e:
            logger.error(f"Erro ao salvar valor no cache: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Remove um valor do cache.
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se o valor foi removido com sucesso, False caso contrário
        """
        if key not in self._metadata["keys"]:
            return False
        
        # Obter caminho do arquivo
        file_path = self._get_file_path(key)
        
        # Remover arquivo
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except IOError as e:
            logger.error(f"Erro ao remover arquivo de cache: {str(e)}")
        
        # Remover chave das tags
        if "tags" in self._metadata["keys"][key]:
            for tag in self._metadata["keys"][key]["tags"]:
                if tag in self._metadata["tags"] and key in self._metadata["tags"][tag]:
                    self._metadata["tags"][tag].remove(key)
        
        # Remover chave dos metadados
        del self._metadata["keys"][key]
        
        self._save_metadata()
        return True
    
    async def clear(self) -> bool:
        """
        Limpa todo o cache.
        
        Returns:
            True se o cache foi limpo com sucesso, False caso contrário
        """
        try:
            # Remover todos os arquivos de cache
            for key in list(self._metadata["keys"].keys()):
                await self.delete(key)
            
            # Limpar metadados
            self._metadata["keys"] = {}
            self._metadata["tags"] = {}
            self._metadata["stats"]["hits"] = 0
            self._metadata["stats"]["misses"] = 0
            
            self._save_metadata()
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False
    
    async def has(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            True se a chave existe, False caso contrário
        """
        # Verificar se a chave existe nos metadados
        if key not in self._metadata["keys"]:
            return False
        
        # Verificar se a chave expirou
        if self._is_expired(key):
            # Expirado, remover e retornar False
            await self.delete(key)
            return False
        
        # Verificar se o arquivo existe
        file_path = self._get_file_path(key)
        return os.path.exists(file_path)
    
    async def ttl(self, key: str) -> Optional[int]:
        """
        Obtém o tempo de vida restante de uma chave.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            Tempo de vida restante em segundos ou None se a chave não existe ou não tem TTL
        """
        if key in self._metadata["keys"] and "expiry" in self._metadata["keys"][key]:
            ttl = self._metadata["keys"][key]["expiry"] - int(time.time())
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
        if not await self.set(key, value, ttl):
            return False
        
        # Remover tags antigas
        if key in self._metadata["keys"] and "tags" in self._metadata["keys"][key]:
            for tag in self._metadata["keys"][key]["tags"]:
                if tag in self._metadata["tags"] and key in self._metadata["tags"][tag]:
                    self._metadata["tags"][tag].remove(key)
        
        # Associar novas tags
        unique_tags = list(set(tags))  # Remover duplicatas
        self._metadata["keys"][key]["tags"] = unique_tags
        
        # Atualizar mapeamentos de tags
        for tag in unique_tags:
            if tag not in self._metadata["tags"]:
                self._metadata["tags"][tag] = []
            
            if key not in self._metadata["tags"][tag]:
                self._metadata["tags"][tag].append(key)
        
        self._save_metadata()
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
        
        if tag in self._metadata["tags"]:
            # Obter todas as chaves associadas à tag
            for key in list(self._metadata["tags"][tag]):
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
        
        if tag in self._metadata["tags"]:
            # Obter todas as chaves associadas à tag
            keys = list(self._metadata["tags"][tag])
            
            # Remover todas as chaves
            for key in keys:
                if await self.delete(key):
                    count += 1
            
            # Limpar a tag
            self._metadata["tags"][tag] = []
            
            self._save_metadata()
        
        return count
    
    async def get_tags(self, key: str) -> List[str]:
        """
        Obtém todas as tags associadas a uma chave.
        
        Args:
            key: Chave para buscar tags
            
        Returns:
            Lista de tags associadas à chave
        """
        if key in self._metadata["keys"] and "tags" in self._metadata["keys"][key]:
            return self._metadata["keys"][key]["tags"]
        return []
    
    async def get_info(self) -> CacheInfo:
        """
        Obtém informações sobre o cache.
        
        Returns:
            Objeto CacheInfo com informações sobre o cache
        """
        # Verificar e remover chaves expiradas
        now = int(time.time())
        for key in list(self._metadata["keys"].keys()):
            if self._is_expired(key):
                await self.delete(key)
        
        # Atualizar estatísticas em memória
        self._metadata["stats"]["hits"] = self._hits
        self._metadata["stats"]["misses"] = self._misses
        
        # Coletar estatísticas adicionais
        stats = {
            "file_count": len(self._metadata["keys"]),
            "tag_count": len(self._metadata["tags"]),
            "cache_dir": self._cache_dir,
            "meta_file_size": os.path.getsize(self._meta_file) if os.path.exists(self._meta_file) else 0,
            "serialization": "pickle" if self._use_pickle else "json"
        }
        
        # Mesclar com estatísticas salvas
        stats.update(self._metadata["stats"])
        
        return CacheInfo(
            provider_name="file",
            item_count=len(self._metadata["keys"]),
            max_size=None,  # Limitado apenas pelo disco
            hits=self._hits,
            misses=self._misses,
            tags=list(self._metadata["tags"].keys()),
            stats=stats
        )
