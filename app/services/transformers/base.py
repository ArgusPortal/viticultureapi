"""
Implementações base de transformadores de dados.
"""
import logging
from typing import Any, List, Dict, Optional, Union
import re

logger = logging.getLogger(__name__)

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
            
            # Skip items with navigation arrows in any quantity field
            if isinstance(item, dict) and any("«‹›»" in str(value) for value in item.values()):
                removed_count += 1
                continue
            
            # Clean up any fields that might contain navigation arrows but weren't caught by the filters above
            if isinstance(item, dict):
                for key in list(item.keys()):
                    if isinstance(item[key], str) and self.nav_arrows_pattern.search(item[key]):
                        # Replace navigation arrows with empty string for any field that might contain them
                        item[key] = self.nav_arrows_pattern.sub('', item[key]).strip()
                        cleaned_values_count += 1
                        
                        # If after cleaning the field is empty, set to None or 0 based on expected type
                        if item[key] == '':
                            if key.startswith('Quantidade') or key in ('Valor', 'Ano'):
                                item[key] = 0
                            else:
                                item[key] = None
                
                # Fix duplicate quantity fields - remove "Quantidade" if "Quantidade (L.)" exists
                if "Quantidade (L.)" in item and "Quantidade" in item:
                    # We're keeping "Quantidade (L.)" and removing "Quantidade"
                    item.pop("Quantidade", None)
                    fixed_fields_count += 1
                
            cleaned_data.append(item)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} navigation arrow entries from data")
            
        if fixed_fields_count > 0:
            logger.info(f"Fixed {fixed_fields_count} items with duplicate quantity fields")
            
        if cleaned_values_count > 0:
            logger.info(f"Cleaned navigation arrows from {cleaned_values_count} field values")
            
        return cleaned_data

class NumericValueCleaner(BaseTransformer):
    """Transformador que limpa e converte valores numéricos."""
    
    def __init__(self, decimal_separator='.', thousand_separator=','):
        self.decimal_separator = decimal_separator
        self.thousand_separator = thousand_separator
    
    def _transform_data(self, data: Any) -> Any:
        """
        Limpa e converte valores numéricos em uma estrutura de dados.
        
        Args:
            data: Dados a serem transformados
            
        Returns:
            Dados com valores numéricos limpos e convertidos
        """
        if isinstance(data, list):
            return [self._transform_data(item) for item in data]
        
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Se o nome da chave indica um valor numérico, tenta converter
                if any(term in key.lower() for term in ['quantidade', 'valor', 'preco', 'volume', 'peso']):
                    result[key] = self._clean_numeric_value(value)
                else:
                    result[key] = self._transform_data(value)
            return result
        
        # Para strings que parecem números, converte diretamente
        if isinstance(data, str) and self._looks_like_number(data):
            return self._clean_numeric_value(data)
        
        # Outros tipos retornam sem alteração
        return data
    
    def _looks_like_number(self, value: str) -> bool:
        """Verifica se uma string parece um número."""
        # Remove separadores de milhares e outros caracteres não numéricos exceto o separador decimal
        cleaned = re.sub(r'[^\d' + re.escape(self.decimal_separator) + r']', '', value)
        # Verifica se a string contém apenas dígitos e no máximo um separador decimal
        return bool(re.match(r'^\d*' + re.escape(self.decimal_separator) + r'?\d*$', cleaned))
    
    def _clean_numeric_value(self, value: Any) -> Union[float, int, Any]:
        """
        Limpa e converte um valor numérico.
        
        Args:
            value: Valor a ser limpo e convertido
            
        Returns:
            Valor numérico limpo ou o valor original se não for possível converter
        """
        if isinstance(value, (int, float)):
            return value
        
        if not isinstance(value, str):
            return value
        
        try:
            # Remove caracteres não numéricos exceto o separador decimal
            cleaned_value = re.sub(r'[^\d' + re.escape(self.decimal_separator) + r']', '', value)
            
            # Converte o separador decimal para ponto
            if self.decimal_separator != '.':
                cleaned_value = cleaned_value.replace(self.decimal_separator, '.')
            
            # Se parece um inteiro, converte para int, senão para float
            if '.' not in cleaned_value:
                return int(cleaned_value) if cleaned_value else 0
            else:
                return float(cleaned_value)
        except (ValueError, TypeError):
            logger.debug(f"Não foi possível converter '{value}' para um valor numérico")
            return value
