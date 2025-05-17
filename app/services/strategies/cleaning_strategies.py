"""
Estratégias de limpeza de dados.

Implementações concretas de estratégias para limpeza de dados específicos da viticultura.
"""
import re
import logging
from typing import Any, Dict, List, Union, Optional
import pandas as pd

from app.services.strategies.base import CleaningStrategy

logger = logging.getLogger(__name__)

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
        if isinstance(data, list):
            return [self.clean(item) for item in data]
            
        if isinstance(data, dict):
            cleaned_dict = {}
            for key, value in data.items():
                if value is None:
                    # Inferir tipo pelo nome da chave
                    if any(term in key.lower() for term in ["quantidade", "valor", "total", "peso"]):
                        cleaned_dict[key] = self.default_num
                    else:
                        cleaned_dict[key] = self.default_str
                elif isinstance(value, str) and value.strip() == "":
                    if any(term in key.lower() for term in ["quantidade", "valor", "total", "peso"]):
                        cleaned_dict[key] = self.default_num
                    else:
                        cleaned_dict[key] = self.default_str
                else:
                    cleaned_dict[key] = self.clean(value) if isinstance(value, (dict, list)) else value
            return cleaned_dict
            
        return data

class OutlierDetectionStrategy(CleaningStrategy):
    """Estratégia para detecção e tratamento de outliers em dados numéricos."""
    
    def __init__(self, method: str = "iqr", threshold: float = 1.5):
        """
        Inicializa a estratégia de detecção de outliers.
        
        Args:
            method: Método de detecção ('iqr' ou 'zscore')
            threshold: Limiar para considerar um valor como outlier
        """
        self.method = method.lower()
        self.threshold = threshold
        
    def clean(self, data: Any) -> Any:
        """
        Detecta e marca outliers nos dados.
        
        Args:
            data: Dados a serem analisados
            
        Returns:
            Dados com outliers marcados
        """
        if not isinstance(data, list) or len(data) < 3:
            return data
            
        # Tentar encontrar campos numéricos para analisar
        numeric_fields = self._identify_numeric_fields(data)
        if not numeric_fields:
            return data
            
        # Analisar cada campo numérico
        result = []
        for item in data:
            if not isinstance(item, dict):
                result.append(item)
                continue
                
            # Criar cópia do item para não modificar o original
            processed_item = dict(item)
            
            for field in numeric_fields:
                if field not in processed_item:
                    continue
                    
                try:
                    value = float(processed_item[field])
                    stats = self._get_field_stats(data, field)
                    
                    # Marcar outliers
                    if self._is_outlier(value, stats):
                        # Adicionar marcação de outlier
                        if "metadata" not in processed_item:
                            processed_item["metadata"] = {}
                        if "outliers" not in processed_item["metadata"]:
                            processed_item["metadata"]["outliers"] = []
                        processed_item["metadata"]["outliers"].append(field)
                except (ValueError, TypeError):
                    # Ignorar valores que não podem ser convertidos para float
                    pass
                    
            result.append(processed_item)
            
        return result
        
    def _identify_numeric_fields(self, data: List[Dict]) -> List[str]:
        """
        Identifica campos numéricos na lista de dados.
        
        Args:
            data: Lista de dicionários de dados
            
        Returns:
            Lista de nomes de campos numéricos
        """
        numeric_fields = set()
        for item in data:
            if not isinstance(item, dict):
                continue
                
            for key, value in item.items():
                try:
                    # Verificar se é um valor numérico
                    if isinstance(value, (int, float)) or (
                        isinstance(value, str) and value.strip() and float(value.replace(',', '.'))
                    ):
                        numeric_fields.add(key)
                except (ValueError, TypeError):
                    # Não é um valor numérico
                    pass
                    
        return list(numeric_fields)
        
    def _get_field_stats(self, data: List[Dict], field: str) -> Dict[str, float]:
        """
        Calcula estatísticas para um campo específico.
        
        Args:
            data: Lista de dicionários de dados
            field: Nome do campo para análise
            
        Returns:
            Dicionário com estatísticas (média, desvio padrão, quartis)
        """
        values = []
        for item in data:
            if not isinstance(item, dict) or field not in item:
                continue
                
            try:
                if isinstance(item[field], (int, float)):
                    values.append(float(item[field]))
                elif isinstance(item[field], str) and item[field].strip():
                    values.append(float(item[field].replace(',', '.')))
            except (ValueError, TypeError):
                # Ignorar valores que não podem ser convertidos
                pass
                
        if not values:
            return {"mean": 0, "std": 0, "q1": 0, "q3": 0, "iqr": 0}
            
        # Calcular estatísticas
        values = sorted(values)
        n = len(values)
        
        # Média e desvio padrão
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = variance ** 0.5
        
        # Quartis
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = values[q1_idx]
        q3 = values[q3_idx]
        iqr = q3 - q1
        
        return {"mean": mean, "std": std, "q1": q1, "q3": q3, "iqr": iqr}
        
    def _is_outlier(self, value: float, stats: Dict[str, float]) -> bool:
        """
        Verifica se um valor é outlier baseado nas estatísticas.
        
        Args:
            value: Valor a ser testado
            stats: Estatísticas do campo
            
        Returns:
            True se é outlier, False caso contrário
        """
        if self.method == "iqr":
            lower_bound = stats["q1"] - self.threshold * stats["iqr"]
            upper_bound = stats["q3"] + self.threshold * stats["iqr"]
            return value < lower_bound or value > upper_bound
            
        elif self.method == "zscore":
            # Se desvio padrão for 0, não há outliers
            if stats["std"] == 0:
                return False
            z_score = abs((value - stats["mean"]) / stats["std"])
            return z_score > self.threshold
            
        # Método desconhecido
        return False
