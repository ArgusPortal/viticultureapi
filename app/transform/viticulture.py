"""
Transformadores específicos para dados de vitivinicultura.

Implementa transformações específicas para os dados de produção,
importação, exportação e processamento de uvas e vinhos.
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import re

from app.core.pipeline import Transformer, DataFrameTransformer, DictTransformer
from app.core.logging import get_logger

logger = get_logger(__name__)

class ProductionDataTransformer(DataFrameTransformer):
    """
    Transformador para dados de produção de vinhos e derivados.
    """
    
    def __init__(self, ano_filtro: Optional[int] = None):
        """
        Inicializa o transformador.
        
        Args:
            ano_filtro: Ano para filtro (opcional)
        """
        super().__init__("production_transformer")
        self.ano_filtro = ano_filtro
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma os dados de produção.
        
        Args:
            data: DataFrame com dados brutos
            
        Returns:
            DataFrame transformado
        """
        # Verificar se temos as colunas esperadas
        required_cols = ["Produto", "Quantidade", "Ano"]
        if not all(col in data.columns for col in required_cols):
            self.logger.warning(f"Colunas necessárias não encontradas. Colunas: {data.columns}")
        
        # Limpar nomes das colunas (remover espaços extras, etc.)
        data = self.clean_column_names(data)
        
        # Converter quantidade para numérico
        if "quantidade" in data.columns:
            data["quantidade"] = pd.to_numeric(data["quantidade"], errors="coerce")
        
        # Converter ano para inteiro
        if "ano" in data.columns:
            data["ano"] = pd.to_numeric(data["ano"], errors="coerce").astype("Int64")
        
        # Filtrar por ano se especificado
        if self.ano_filtro and "ano" in data.columns:
            data = data[data["ano"] == self.ano_filtro]
        
        # Ordenar por ano e produto
        sort_cols = []
        if "ano" in data.columns:
            sort_cols.append("ano")
        if "produto" in data.columns:
            sort_cols.append("produto")
        
        if sort_cols:
            data = data.sort_values(by=sort_cols)
        
        # Remover duplicatas
        data = self.drop_duplicates(data)
        
        # Remover linhas com quantidade nula
        data = data.dropna(subset=["quantidade"] if "quantidade" in data.columns else None)
        
        return data
    
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e padroniza nomes de colunas.
        
        Args:
            df: DataFrame
            
        Returns:
            DataFrame com nomes de colunas limpos
        """
        # Converter para minúsculas e remover espaços
        rename_map = {col: col.lower().strip() for col in df.columns}
        
        # Mapeamentos específicos
        specific_map = {
            "produto": "produto",
            "quantidade (l.)": "quantidade",
            "quantidade(l.)": "quantidade",
            "quantidade": "quantidade",
            "ano": "ano"
        }
        
        # Aplicar mapeamentos específicos onde aplicável
        for old, new in specific_map.items():
            if old in rename_map.values():
                # Encontrar a chave original
                for k, v in rename_map.items():
                    if v == old:
                        rename_map[k] = new
                        break
        
        return self.rename_columns(df, rename_map)

class ImportExportTransformer(DataFrameTransformer):
    """
    Transformador para dados de importação e exportação.
    """
    
    def __init__(self, ano_filtro: Optional[int] = None, pais_filtro: Optional[str] = None):
        """
        Inicializa o transformador.
        
        Args:
            ano_filtro: Ano para filtro (opcional)
            pais_filtro: País para filtro (opcional)
        """
        super().__init__("import_export_transformer")
        self.ano_filtro = ano_filtro
        self.pais_filtro = pais_filtro
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma os dados de importação/exportação.
        
        Args:
            data: DataFrame com dados brutos
            
        Returns:
            DataFrame transformado
        """
        # Verificar se temos as colunas esperadas
        required_cols = ["Pais", "Produto", "Quantidade", "Valor", "Ano"]
        if not all(col in data.columns for col in required_cols):
            self.logger.warning(f"Colunas necessárias não encontradas. Colunas: {data.columns}")
        
        # Limpar nomes das colunas
        data = self.clean_column_names(data)
        
        # Converter quantidade e valor para numérico
        for col in ["quantidade", "valor"]:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors="coerce")
        
        # Converter ano para inteiro
        if "ano" in data.columns:
            data["ano"] = pd.to_numeric(data["ano"], errors="coerce").astype("Int64")
        
        # Filtrar por ano se especificado
        if self.ano_filtro and "ano" in data.columns:
            data = data[data["ano"] == self.ano_filtro]
        
        # Filtrar por país se especificado
        if self.pais_filtro and "pais" in data.columns:
            pattern = re.compile(self.pais_filtro, re.IGNORECASE)
            data = data[data["pais"].str.contains(pattern, na=False)]
        
        # Ordenar por ano, país e produto
        sort_cols = []
        for col in ["ano", "pais", "produto"]:
            if col in data.columns:
                sort_cols.append(col)
        
        if sort_cols:
            data = data.sort_values(by=sort_cols)
        
        # Remover duplicatas
        data = self.drop_duplicates(data)
        
        # Remover linhas com valores nulos
        for col in ["quantidade", "valor"]:
            if col in data.columns:
                data = data.dropna(subset=[col])
        
        return data
    
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e padroniza nomes de colunas.
        
        Args:
            df: DataFrame
            
        Returns:
            DataFrame com nomes de colunas limpos
        """
        # Converter para minúsculas e remover espaços
        rename_map = {col: col.lower().strip() for col in df.columns}
        
        # Mapeamentos específicos
        specific_map = {
            "pais": "pais",
            "país": "pais",
            "produto": "produto",
            "quantidade": "quantidade",
            "valor": "valor",
            "valor (us$)": "valor",
            "ano": "ano"
        }
        
        # Aplicar mapeamentos específicos onde aplicável
        for old, new in specific_map.items():
            if old in rename_map.values():
                # Encontrar a chave original
                for k, v in rename_map.items():
                    if v == old:
                        rename_map[k] = new
                        break
        
        return self.rename_columns(df, rename_map)

class ProcessingTransformer(DataFrameTransformer):
    """
    Transformador para dados de processamento de uvas.
    """
    
    def __init__(self, ano_filtro: Optional[int] = None):
        """
        Inicializa o transformador.
        
        Args:
            ano_filtro: Ano para filtro (opcional)
        """
        super().__init__("processing_transformer")
        self.ano_filtro = ano_filtro
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma os dados de processamento.
        
        Args:
            data: DataFrame com dados brutos
            
        Returns:
            DataFrame transformado
        """
        # Verificar se temos as colunas esperadas
        required_cols = ["Grupo", "Quantidade (kg)", "Ano"]
        if not all(col in data.columns for col in required_cols):
            self.logger.warning(f"Colunas necessárias não encontradas. Colunas: {data.columns}")
        
        # Limpar nomes das colunas
        data = self.clean_column_names(data)
        
        # Converter quantidade para numérico
        if "quantidade" in data.columns:
            data["quantidade"] = pd.to_numeric(data["quantidade"], errors="coerce")
        
        # Converter ano para inteiro
        if "ano" in data.columns:
            data["ano"] = pd.to_numeric(data["ano"], errors="coerce").astype("Int64")
        
        # Filtrar por ano se especificado
        if self.ano_filtro and "ano" in data.columns:
            data = data[data["ano"] == self.ano_filtro]
        
        # Ordenar por ano e grupo
        sort_cols = []
        for col in ["ano", "grupo"]:
            if col in data.columns:
                sort_cols.append(col)
        
        if sort_cols:
            data = data.sort_values(by=sort_cols)
        
        # Remover duplicatas
        data = self.drop_duplicates(data)
        
        # Remover linhas com quantidade nula
        if "quantidade" in data.columns:
            data = data.dropna(subset=["quantidade"])
        
        return data
    
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e padroniza nomes de colunas.
        
        Args:
            df: DataFrame
            
        Returns:
            DataFrame com nomes de colunas limpos
        """
        # Converter para minúsculas e remover espaços
        rename_map = {col: col.lower().strip() for col in df.columns}
        
        # Mapeamentos específicos
        specific_map = {
            "grupo": "grupo",
            "quantidade (kg)": "quantidade",
            "quantidade(kg)": "quantidade",
            "ano": "ano",
            "variedade": "variedade"
        }
        
        # Aplicar mapeamentos específicos onde aplicável
        for old, new in specific_map.items():
            if old in rename_map.values():
                # Encontrar a chave original
                for k, v in rename_map.items():
                    if v == old:
                        rename_map[k] = new
                        break
        
        return self.rename_columns(df, rename_map)

class CommercializationTransformer(DataFrameTransformer):
    """
    Transformador para dados de comercialização no mercado interno.
    """
    
    def __init__(self, ano_filtro: Optional[int] = None):
        """
        Inicializa o transformador.
        
        Args:
            ano_filtro: Ano para filtro (opcional)
        """
        super().__init__("commercialization_transformer")
        self.ano_filtro = ano_filtro
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma os dados de comercialização.
        
        Args:
            data: DataFrame com dados brutos
            
        Returns:
            DataFrame transformado
        """
        # Verificar se temos as colunas esperadas
        required_cols = ["Produto", "Quantidade (L.)", "Ano"]
        if not all(col in data.columns for col in required_cols):
            self.logger.warning(f"Colunas necessárias não encontradas. Colunas: {data.columns}")
        
        # Limpar nomes das colunas
        data = self.clean_column_names(data)
        
        # Converter quantidade para numérico
        if "quantidade" in data.columns:
            data["quantidade"] = pd.to_numeric(data["quantidade"], errors="coerce")
        
        # Converter ano para inteiro
        if "ano" in data.columns:
            data["ano"] = pd.to_numeric(data["ano"], errors="coerce").astype("Int64")
        
        # Filtrar por ano se especificado
        if self.ano_filtro and "ano" in data.columns:
            data = data[data["ano"] == self.ano_filtro]
        
        # Ordenar por ano e produto
        sort_cols = []
        for col in ["ano", "produto"]:
            if col in data.columns:
                sort_cols.append(col)
        
        if sort_cols:
            data = data.sort_values(by=sort_cols)
        
        # Remover duplicatas
        data = self.drop_duplicates(data)
        
        # Remover linhas com quantidade nula
        if "quantidade" in data.columns:
            data = data.dropna(subset=["quantidade"])
        
        return data
    
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e padroniza nomes de colunas.
        
        Args:
            df: DataFrame
            
        Returns:
            DataFrame com nomes de colunas limpos
        """
        # Converter para minúsculas e remover espaços
        rename_map = {col: col.lower().strip() for col in df.columns}
        
        # Mapeamentos específicos
        specific_map = {
            "produto": "produto",
            "quantidade (l.)": "quantidade",
            "quantidade(l.)": "quantidade",
            "ano": "ano"
        }
        
        # Aplicar mapeamentos específicos onde aplicável
        for old, new in specific_map.items():
            if old in rename_map.values():
                # Encontrar a chave original
                for k, v in rename_map.items():
                    if v == old:
                        rename_map[k] = new
                        break
        
        return self.rename_columns(df, rename_map)

class DataFrameToDictTransformer(Transformer[pd.DataFrame, Dict[str, Any]]):
    """
    Transforma um DataFrame em um dicionário estruturado para API.
    """
    
    def __init__(
        self,
        source: str = "pipeline", 
        ano_filtro: Optional[int] = None,
        pais_filtro: Optional[str] = None,
        include_source_url: bool = True,
        source_url: Optional[str] = None
    ):
        """
        Inicializa o transformador.
        
        Args:
            source: Fonte dos dados (scraping, csv, etc.)
            ano_filtro: Ano filtrado (opcional)
            pais_filtro: País filtrado (opcional)
            include_source_url: Se deve incluir URL da fonte
            source_url: URL da fonte dos dados (opcional)
        """
        self.source = source
        self.ano_filtro = ano_filtro
        self.pais_filtro = pais_filtro
        self.include_source_url = include_source_url
        self.source_url = source_url
        self.logger = get_logger("transformer.df_to_dict")
    
    def transform(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Transforma o DataFrame em um dicionário.
        
        Args:
            data: DataFrame de entrada
            
        Returns:
            Dicionário estruturado
        """
        self.logger.info(f"Convertendo DataFrame para dicionário: {len(data)} linhas")
        
        # Converter DataFrame para lista de dicionários
        records = data.to_dict(orient="records")
        
        # Criar estrutura da resposta
        result = {
            "source": self.source,
            "timestamp": datetime.now().isoformat(),
            "data": records,
            "count": len(records)
        }
        
        # Adicionar informações de filtro se aplicável
        if self.ano_filtro:
            result["ano_filtro"] = self.ano_filtro
        
        if self.pais_filtro:
            result["pais_filtro"] = self.pais_filtro
        
        # Adicionar URL da fonte se disponível
        if self.include_source_url and self.source_url:
            result["source_url"] = self.source_url
        
        return result
