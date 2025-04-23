"""
Utilitários para limpeza e transformação de dados.

Este módulo contém funções para limpar e transformar dados
obtidos por scraping ou outras fontes.
"""
import logging
import re
from typing import List, Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

def clean_navigation_arrows(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove navigation arrow entries from scraped data results and fix data structure.
    
    This function:
    1. Removes navigation arrow entries ("«‹›»")
    2. Fixes duplicate quantity fields by keeping only "Quantidade (L.)" when both are present
    3. Cleans navigation arrows from quantity values before they cause conversion errors
    
    Args:
        data_list: Lista de dicionários com dados a serem limpos
        
    Returns:
        Lista de dicionários com dados limpos
    """
    if not data_list or not isinstance(data_list, list):
        return data_list
    
    cleaned_data = []
    removed_count = 0
    fixed_fields_count = 0
    cleaned_values_count = 0
    
    # Regular expression to detect navigation arrows
    nav_arrows_pattern = re.compile(r'[«‹›»]')
    
    for item in data_list:
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
            for key in item:
                if isinstance(item[key], str) and nav_arrows_pattern.search(item[key]):
                    # Replace navigation arrows with empty string for any field that might contain them
                    item[key] = nav_arrows_pattern.sub('', item[key]).strip()
                    cleaned_values_count += 1
                    
                    # If after cleaning the field is empty, set to None or 0 based on expected type
                    if item[key] == '':
                        if key.startswith('Quantidade') or key in ('Valor', 'Ano'):
                            item[key] = 0
                        else:
                            item[key] = None
        
        # Fix duplicate quantity fields - remove "Quantidade" if "Quantidade (L.)" exists
        if isinstance(item, dict) and "Quantidade (L.)" in item and "Quantidade" in item:
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

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float, handling navigation arrows and other invalid formats.
    Returns the default value if conversion fails.
    
    Args:
        value: Valor a ser convertido
        default: Valor padrão caso a conversão falhe
        
    Returns:
        Valor convertido para float ou valor padrão
    """
    if value is None:
        return default
        
    if isinstance(value, (int, float)):
        return float(value)
        
    if isinstance(value, str):
        # Remove navigation arrows and any non-numeric characters except decimal separator
        cleaned_value = re.sub(r'[^0-9\.,]', '', value.replace('«‹›»', ''))
        
        # Handle different decimal separators
        cleaned_value = cleaned_value.replace(',', '.')
        
        # If we have a valid string after cleaning, try to convert it
        if cleaned_value:
            try:
                return float(cleaned_value)
            except ValueError:
                logger.debug(f"Could not convert '{value}' to float even after cleaning")
        
    logger.warning(f"Could not convert '{value}' to float, using default {default}")
    return default

