"""
Sistema de normalização de dados.

Fornece normalizadores para padronizar diferentes tipos de dados.
"""
import re
import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union, cast
import unicodedata

from app.core.validation.interface import (
    Normalizer, ValidationResult, ValidationIssue, ValidationSeverity
)
from app.core.validation.validators import (
    StringValidator, NumericValidator, DateValidator
)

class StringNormalizer(Normalizer[str, str]):
    """Normalizador para strings."""
    
    def __init__(
        self,
        field_name: str,
        strip: bool = True,
        lowercase: bool = False,
        uppercase: bool = False,
        remove_accents: bool = False,
        replace_pattern: Optional[Tuple[str, str]] = None,
        validator: Optional[StringValidator] = None
    ):
        """
        Inicializa o normalizador de strings.
        
        Args:
            field_name: Nome do campo sendo normalizado
            strip: Remove espaços no início e fim
            lowercase: Converte para minúsculas
            uppercase: Converte para maiúsculas
            remove_accents: Remove acentos
            replace_pattern: (padrão, substituto) para substituições via regex
            validator: Validador a ser aplicado após normalização
        """
        self.field_name = field_name
        self.strip = strip
        self.lowercase = lowercase
        self.uppercase = uppercase
        self.remove_accents = remove_accents
        self.replace_pattern = replace_pattern
        self.validator = validator or StringValidator(field_name)
    
    def _remove_accents_from_string(self, text: str) -> str:
        """Remove acentos de uma string."""
        return ''.join(
            c for c in unicodedata.normalize('NFKD', text)
            if not unicodedata.combining(c)
        )
    
    def normalize(self, data: Optional[str]) -> Tuple[str, ValidationResult]:
        """
        Normaliza uma string.
        
        Args:
            data: String a ser normalizada
            
        Returns:
            Tuple com a string normalizada e o resultado da validação
        """
        result = ValidationResult()
        
        # Se for None, não há como normalizar
        if data is None:
            # Validate para verificar se é permitido ser None
            result = self.validator.validate(None)
            return "", result  # Return empty string instead of None
        
        normalized_data = data
        
        # Aplicar normalizações
        if self.strip:
            normalized_data = normalized_data.strip()
        
        if self.lowercase:
            normalized_data = normalized_data.lower()
        
        if self.uppercase:
            normalized_data = normalized_data.upper()
        
        if self.remove_accents:
            normalized_data = self._remove_accents_from_string(normalized_data)
        
        if self.replace_pattern:
            pattern, replacement = self.replace_pattern
            normalized_data = re.sub(pattern, replacement, normalized_data)
        
        # Validar após normalização
        result = self.validator.validate(normalized_data)
        
        return normalized_data, result

class NumericNormalizer(Normalizer[Any, Union[int, float]]):
    """Normalizador para valores numéricos."""
    
    def __init__(
        self,
        field_name: str,
        decimal_places: Optional[int] = None,
        default_value: Optional[Union[int, float]] = None,
        convert_empty_to_none: bool = False,
        convert_none_to_zero: bool = False,
        validator: Optional[NumericValidator] = None
    ):
        """
        Inicializa o normalizador numérico.
        
        Args:
            field_name: Nome do campo sendo normalizado
            decimal_places: Número de casas decimais (arredondamento)
            default_value: Valor padrão para casos de erro
            convert_empty_to_none: Converte strings vazias para None
            convert_none_to_zero: Converte None para 0
            validator: Validador a ser aplicado após normalização
        """
        self.field_name = field_name
        self.decimal_places = decimal_places
        self.default_value = default_value
        self.convert_empty_to_none = convert_empty_to_none
        self.convert_none_to_zero = convert_none_to_zero
        self.validator = validator or NumericValidator(field_name)
    
    def normalize(self, data: Any) -> Tuple[Union[int, float], ValidationResult]:
        """
        Normaliza um valor numérico.
        
        Args:
            data: Valor a ser normalizado (pode ser string, int, float, etc.)
            
        Returns:
            Tuple com o valor normalizado e o resultado da validação
        """
        result = ValidationResult()
        
        # Tratar None e strings vazias
        if data is None:
            if self.convert_none_to_zero:
                return 0, self.validator.validate(0)
            
            # Return default value (0) instead of None
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="Valor nulo não permitido",
                severity=ValidationSeverity.ERROR,
                value=None
            ))
            return 0 if self.default_value is None else self.default_value, result
        
        if isinstance(data, str) and data.strip() == "":
            if self.convert_empty_to_none:
                return 0, self.validator.validate(None)
            
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="String vazia não pode ser convertida para número",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
            return 0 if self.default_value is None else self.default_value, result
        
        # Tentar converter para número
        try:
            if isinstance(data, str):
                # Remover caracteres não numéricos, exceto ponto decimal e sinal negativo
                cleaned = re.sub(r'[^\d.-]', '', data.replace(',', '.'))
                numeric_value = float(cleaned)
            else:
                numeric_value = float(data)
            
            # Aplicar arredondamento se necessário
            if self.decimal_places is not None:
                numeric_value = round(numeric_value, self.decimal_places)
            
            # Converter para int se for um número inteiro
            if numeric_value.is_integer():
                numeric_value = int(numeric_value)
            
            # Validar após normalização
            result = self.validator.validate(numeric_value)
            return numeric_value, result
            
        except (ValueError, TypeError) as e:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"Valor não pode ser convertido para número: {str(e)}",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
            return 0 if self.default_value is None else self.default_value, result

class DateNormalizer(Normalizer[Any, Union[datetime, str]]):
    """Normalizador para datas."""
    
    def __init__(
        self,
        field_name: str,
        input_formats: List[str] = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"],
        output_format: Optional[str] = None,
        validator: Optional[DateValidator] = None
    ):
        """
        Inicializa o normalizador de datas.
        
        Args:
            field_name: Nome do campo sendo normalizado
            input_formats: Formatos de entrada aceitos, em ordem de tentativa
            output_format: Formato para retorno como string (se None, retorna datetime)
            validator: Validador a ser aplicado após normalização
        """
        self.field_name = field_name
        self.input_formats = input_formats
        self.output_format = output_format
        self.validator = validator or DateValidator(field_name)
    
    def normalize(self, data: Any) -> Tuple[Union[datetime, str], ValidationResult]:
        """
        Normaliza uma data.
        
        Args:
            data: Data a ser normalizada (string, datetime, etc.)
            
        Returns:
            Tuple com a data normalizada e o resultado da validação
        """
        result = ValidationResult()
        
        # Tratar None
        if data is None:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="Data não fornecida (None)",
                severity=ValidationSeverity.ERROR,
                value=None
            ))
            # Return a default date instead of None
            default_date = datetime.now()
            return default_date if not self.output_format else default_date.strftime(self.output_format), result
        
        # Se já for datetime, usar diretamente
        if isinstance(data, datetime):
            normalized_date = data
        else:
            # Tentar converter string para datetime usando os formatos fornecidos
            if isinstance(data, str):
                date_str = data.strip()
                normalized_date = None
                
                for fmt in self.input_formats:
                    try:
                        normalized_date = datetime.strptime(date_str, fmt)
                        break  # Encontrou um formato válido
                    except ValueError:
                        continue  # Tentar próximo formato
                
                if normalized_date is None:
                    result.add_issue(ValidationIssue(
                        field=self.field_name,
                        message=f"Data em formato não reconhecido. Formatos válidos: {', '.join(self.input_formats)}",
                        severity=ValidationSeverity.ERROR,
                        value=data
                    ))
                    return datetime.now(), result
            else:
                result.add_issue(ValidationIssue(
                    field=self.field_name,
                    message=f"Tipo de dados não pode ser convertido para data: {type(data).__name__}",
                    severity=ValidationSeverity.ERROR,
                    value=data
                ))
                return datetime.now(), result
        
        # Validar após normalização
        val_result = self.validator.validate(normalized_date)
        result.merge(val_result)
        
        # Converter para string se necessário
        if self.output_format and result.is_valid:
            return normalized_date.strftime(self.output_format), result
        
        return normalized_date, result

class DictNormalizer(Normalizer[Dict[str, Any], Dict[str, Any]]):
    """Normalizador para dicionários."""
    
    def __init__(
        self,
        field_name: str,
        field_normalizers: Dict[str, Normalizer[Any, Any]],
        remove_extra_fields: bool = False,
        add_missing_fields: bool = False,
        default_values: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa o normalizador de dicionários.
        
        Args:
            field_name: Nome do campo sendo normalizado
            field_normalizers: Dicionário de normalizadores por campo
            remove_extra_fields: Se deve remover campos não definidos nos normalizadores
            add_missing_fields: Se deve adicionar campos ausentes com valores padrão
            default_values: Valores padrão para campos ausentes
        """
        self.field_name = field_name
        self.field_normalizers = field_normalizers
        self.remove_extra_fields = remove_extra_fields
        self.add_missing_fields = add_missing_fields
        self.default_values = default_values or {}
    
    def normalize(self, data: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], ValidationResult]:
        """
        Normaliza um dicionário.
        
        Args:
            data: Dicionário a ser normalizado
            
        Returns:
            Tuple com o dicionário normalizado e o resultado da validação
        """
        result = ValidationResult()
        
        # Tratar None
        if data is None:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="Dicionário não fornecido (None)",
                severity=ValidationSeverity.ERROR
            ))
            return {}, result  # Return empty dict instead of None
        
        normalized_data = {}
        
        # Normalizar campos presentes
        for field, value in data.items():
            # Se o campo não tem normalizador e devemos remover campos extras
            if field not in self.field_normalizers:
                if not self.remove_extra_fields:
                    normalized_data[field] = value  # Manter o campo original
                continue
            
            # Normalizar o campo
            normalizer = self.field_normalizers[field]
            normalized_value, field_result = normalizer.normalize(value)
            
            # Adicionar prefixo de campo pai aos problemas
            for issue in field_result.issues:
                issue.field = f"{self.field_name}.{issue.field}"
                result.add_issue(issue)
            
            normalized_data[field] = normalized_value
        
        # Adicionar campos ausentes com valores padrão
        if self.add_missing_fields:
            for field in self.field_normalizers:
                if field not in normalized_data:
                    default_value = self.default_values.get(field)
                    normalizer = self.field_normalizers[field]
                    normalized_value, field_result = normalizer.normalize(default_value)
                    
                    # Adicionar prefixo de campo pai aos problemas
                    for issue in field_result.issues:
                        issue.field = f"{self.field_name}.{issue.field}"
                        result.add_issue(issue)
                    
                    normalized_data[field] = normalized_value
        
        return normalized_data, result

class DataFrameColumnNormalizer:
    """Normaliza colunas específicas de um DataFrame."""
    
    def __init__(
        self,
        column_normalizers: Dict[str, Normalizer[Any, Any]]
    ):
        """
        Inicializa o normalizador de colunas de DataFrame.
        
        Args:
            column_normalizers: Dicionário de normalizadores por coluna
        """
        self.column_normalizers = column_normalizers
    
    def normalize_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[ValidationIssue]]]:
        """
        Normaliza um DataFrame coluna a coluna.
        
        Args:
            df: DataFrame a ser normalizado
            
        Returns:
            Tuple com o DataFrame normalizado e um dicionário de problemas por coluna
        """
        normalized_df = df.copy()
        issues_by_column = {}
        
        for column, normalizer in self.column_normalizers.items():
            if column in df.columns:
                column_issues = []
                
                # Normalizar cada valor na coluna
                for idx, value in enumerate(df[column]):
                    normalized_value, val_result = normalizer.normalize(value)
                    
                    # Se houver problemas, adicionar o índice da linha
                    for issue in val_result.issues:
                        issue.field = f"{column}[{idx}]"
                        column_issues.append(issue)
                    
                    # Atualizar o valor normalizado
                    normalized_df.at[idx, column] = normalized_value
                
                if column_issues:
                    issues_by_column[column] = column_issues
        
        return normalized_df, issues_by_column
