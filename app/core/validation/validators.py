"""
Implementações concretas de validadores.

Este módulo fornece validadores específicos para diferentes tipos de dados,
implementando a interface Validator. Os validadores permitem verificar
a conformidade dos dados com regras específicas e gerar resultados
de validação estruturados.

Classes:
    StringValidator: Validador para strings com regras como comprimento e padrões
    NumericValidator: Validador para valores numéricos com regras como min/max
    DateValidator: Validador para datas com regras como intervalo de datas
    DictValidator: Validador para dicionários seguindo um schema
    ListValidator: Validador para listas com validação de itens
    DataFrameValidator: Validador para DataFrames pandas
"""
import re
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional, Pattern, Union

from app.core.validation.interface import (
    Validator, ValidationResult, ValidationIssue, ValidationSeverity, validate_common
)

class StringValidator(Validator[str]):
    """
    Validador para strings.
    
    Verifica se uma string atende a critérios como comprimento mínimo/máximo,
    conformidade com um padrão regex e presença em um conjunto de valores permitidos.
    
    Attributes:
        field_name: Nome do campo sendo validado
        min_length: Comprimento mínimo permitido
        max_length: Comprimento máximo permitido
        pattern: Padrão regex compilado para validação
        required: Se a string é obrigatória
        allow_empty: Se strings vazias são permitidas
        allowed_values: Lista de valores permitidos
    
    Example:
        >>> validator = StringValidator("nome", min_length=3, pattern=r'^[a-z]+$')
        >>> result = validator.validate("abc")
        >>> result.is_valid
        True
    """
    
    def __init__(
        self,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        required: bool = True,
        allow_empty: bool = False,
        allowed_values: Optional[List[str]] = None
    ):
        """
        Inicializa o validador de strings.
        
        Args:
            field_name: Nome do campo sendo validado
            min_length: Comprimento mínimo (opcional)
            max_length: Comprimento máximo (opcional)
            pattern: Padrão regex para validação (opcional)
            required: Se a string é obrigatória
            allow_empty: Se strings vazias são permitidas
            allowed_values: Lista de valores permitidos (opcional)
        """
        self.field_name = field_name
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.required = required
        self.allow_empty = allow_empty
        self.allowed_values = allowed_values
    
    def validate(self, data: Optional[str]) -> ValidationResult:
        """
        Valida uma string.
        
        Args:
            data: String a ser validada
            
        Returns:
            Resultado da validação
        """
        # Usar a função utilitária para validações comuns
        result, should_continue = validate_common(
            data, self.field_name, self.required
        )
        
        if not should_continue:
            return result
        
        # Explicit null check to satisfy type checker
        if data is None:
            return result
        
        # Verificar se é string vazia
        if data == "" and not self.allow_empty:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="String vazia não permitida",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
            return result
        
        # Verificar comprimento mínimo
        if self.min_length is not None and len(data) < self.min_length:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"String tem comprimento menor que o mínimo permitido ({self.min_length})",
                severity=ValidationSeverity.ERROR,
                value=data,
                details={"min_length": self.min_length, "actual_length": len(data)}
            ))
        
        # Verificar comprimento máximo
        if self.max_length is not None and len(data) > self.max_length:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"String excede o comprimento máximo permitido ({self.max_length})",
                severity=ValidationSeverity.ERROR,
                value=data,
                details={"max_length": self.max_length, "actual_length": len(data)}
            ))
        
        # Verificar padrão regex
        if self.pattern and not self.pattern.match(data):
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"String não corresponde ao padrão exigido",
                severity=ValidationSeverity.ERROR,
                value=data,
                details={"pattern": self.pattern.pattern}
            ))
        
        # Verificar valores permitidos
        if self.allowed_values and data not in self.allowed_values:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"Valor não está entre os valores permitidos",
                severity=ValidationSeverity.ERROR,
                value=data,
                details={"allowed_values": self.allowed_values}
            ))
        
        return result


class NumericValidator(Validator[Union[int, float]]):
    """
    Validador para valores numéricos.
    
    Verifica se um número atende a critérios como valor mínimo/máximo,
    se é inteiro quando necessário, e se é positivo ou não-zero quando exigido.
    
    Attributes:
        field_name: Nome do campo sendo validado
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido
        required: Se o valor é obrigatório
        allow_zero: Se zero é permitido
        allow_negative: Se valores negativos são permitidos
        is_integer: Se o valor deve ser inteiro
    
    Example:
        >>> validator = NumericValidator("idade", min_value=0, max_value=120, is_integer=True)
        >>> result = validator.validate(25)
        >>> result.is_valid
        True
    """
    
    def __init__(
        self,
        field_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        required: bool = True,
        allow_zero: bool = True,
        allow_negative: bool = True,
        is_integer: bool = False
    ):
        """
        Inicializa o validador numérico.
        
        Args:
            field_name: Nome do campo sendo validado
            min_value: Valor mínimo permitido (opcional)
            max_value: Valor máximo permitido (opcional)
            required: Se o valor é obrigatório
            allow_zero: Se zero é permitido
            allow_negative: Se valores negativos são permitidos
            is_integer: Se o valor deve ser um inteiro
        """
        self.field_name = field_name
        self.min_value = min_value
        self.max_value = max_value
        self.required = required
        self.allow_zero = allow_zero
        self.allow_negative = allow_negative
        self.is_integer = is_integer
    
    def validate(self, data: Optional[Union[int, float]]) -> ValidationResult:
        """Valida um valor numérico."""
        # Usar a função utilitária para validações comuns
        result, should_continue = validate_common(
            data, self.field_name, self.required
        )
        
        if not should_continue:
            return result
            
        # Ensure data is not None before performing any comparisons
        # This additional check is needed to satisfy the type checker
        if data is None:
            return result
        
        # Check for NaN values before integer validation
        if isinstance(data, float) and pd.isna(data):
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="Valor numérico contém NaN (não é um número)",
                severity=ValidationSeverity.ERROR,
                value="NaN"
            ))
            return result
        
        # Verificar se é inteiro quando necessário
        if self.is_integer and not isinstance(data, int) and int(data) != data:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="Valor deve ser um número inteiro",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
        
        # Verificar valor zero
        if data == 0 and not self.allow_zero:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="Valor zero não permitido",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
        
        # Verificar valor negativo
        if data < 0 and not self.allow_negative:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="Valor negativo não permitido",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
        
        # Verificar valor mínimo
        if self.min_value is not None and data < self.min_value:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"Valor menor que o mínimo permitido ({self.min_value})",
                severity=ValidationSeverity.ERROR,
                value=data,
                details={"min_value": self.min_value}
            ))
        
        # Verificar valor máximo
        if self.max_value is not None and data > self.max_value:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"Valor maior que o máximo permitido ({self.max_value})",
                severity=ValidationSeverity.ERROR,
                value=data,
                details={"max_value": self.max_value}
            ))
        
        return result


class DateValidator(Validator[Union[str, datetime]]):
    """
    Validador para datas.
    
    Verifica se uma data (string ou objeto datetime) está dentro de um intervalo
    específico e segue o formato esperado quando fornecida como string.
    
    Attributes:
        field_name: Nome do campo sendo validado
        min_date: Data mínima permitida
        max_date: Data máxima permitida
        format: Formato da data para strings (padrão: %Y-%m-%d)
        required: Se a data é obrigatória
    
    Example:
        >>> validator = DateValidator("data_nascimento", min_date="1900-01-01")
        >>> result = validator.validate("2000-01-01")
        >>> result.is_valid
        True
    """
    
    def __init__(
        self,
        field_name: str,
        min_date: Optional[Union[str, datetime]] = None,
        max_date: Optional[Union[str, datetime]] = None,
        format: str = "%Y-%m-%d",
        required: bool = True
    ):
        """
        Inicializa o validador de datas.
        
        Args:
            field_name: Nome do campo sendo validado
            min_date: Data mínima permitida (opcional)
            max_date: Data máxima permitida (opcional)
            format: Formato da data para strings
            required: Se o valor é obrigatório
        """
        self.field_name = field_name
        self.format = format
        self.required = required
        
        # Converter strings para datetime
        self.min_date = self._parse_date(min_date) if min_date else None
        self.max_date = self._parse_date(max_date) if max_date else None
    
    def _parse_date(self, date_value: Union[str, datetime]) -> datetime:
        """Converte string para datetime se necessário."""
        if isinstance(date_value, str):
            return datetime.strptime(date_value, self.format)
        return date_value
    
    def validate(self, data: Optional[Union[str, datetime]]) -> ValidationResult:
        """Valida uma data."""
        # Usar a função utilitária para validações comuns
        result, should_continue = validate_common(
            data, self.field_name, self.required
        )
        
        if not should_continue:
            return result
        
        # Converter para datetime se for string
        try:
            if isinstance(data, str):
                date_obj = datetime.strptime(data, self.format)
            else:
                date_obj = data
                
            # Explicit check to ensure date_obj is not None before comparison
            if date_obj is None:
                return result
                
            # Verificar data mínima
            if self.min_date and date_obj < self.min_date:
                result.add_issue(ValidationIssue(
                    field=self.field_name,
                    message=f"Data anterior à data mínima permitida ({self.min_date.strftime(self.format)})",
                    severity=ValidationSeverity.ERROR,
                    value=data,
                    details={"min_date": self.min_date.strftime(self.format)}
                ))
            
            # Verificar data máxima
            if self.max_date and date_obj > self.max_date:
                result.add_issue(ValidationIssue(
                    field=self.field_name,
                    message=f"Data posterior à data máxima permitida ({self.max_date.strftime(self.format)})",
                    severity=ValidationSeverity.ERROR,
                    value=data,
                    details={"max_date": self.max_date.strftime(self.format)}
                ))
        
        except ValueError:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"Formato de data inválido. Esperado: {self.format}",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
            return result
        
        return result

class DictValidator(Validator[Dict[str, Any]]):
    """
    Validador para dicionários.
    
    Verifica se um dicionário segue um schema predefinido, aplicando validadores
    específicos a cada campo e opcionalmente restringindo campos extras.
    
    Attributes:
        field_name: Nome do campo sendo validado
        schema: Dicionário de validadores para cada campo
        required: Se o dicionário é obrigatório
        allow_extra_fields: Se permite campos não definidos no schema
    
    Example:
        >>> schema = {
        ...     "nome": StringValidator("nome", min_length=2),
        ...     "idade": NumericValidator("idade", min_value=0, is_integer=True)
        ... }
        >>> validator = DictValidator("pessoa", schema=schema)
        >>> result = validator.validate({"nome": "Ana", "idade": 30})
        >>> result.is_valid
        True
    """
    
    def __init__(
        self,
        field_name: str,
        schema: Dict[str, Validator[Any]],
        required: bool = True,
        allow_extra_fields: bool = False
    ):
        """
        Inicializa o validador de dicionários.
        
        Args:
            field_name: Nome do campo sendo validado
            schema: Dicionário com validadores para cada campo
            required: Se o dicionário é obrigatório
            allow_extra_fields: Se permite campos não definidos no schema
        """
        self.field_name = field_name
        self.schema = schema
        self.required = required
        self.allow_extra_fields = allow_extra_fields
    
    def validate(self, data: Optional[Dict[str, Any]]) -> ValidationResult:
        """Valida um dicionário conforme o schema definido."""
        result = ValidationResult()
        
        # Verificar se é None quando obrigatório
        if data is None:
            if self.required:
                result.add_issue(ValidationIssue(
                    field=self.field_name,
                    message="Dicionário obrigatório não fornecido",
                    severity=ValidationSeverity.ERROR
                ))
            return result
        
        # Verificar campos não permitidos
        if not self.allow_extra_fields:
            extra_fields = [field for field in data if field not in self.schema]
            if extra_fields:
                result.add_issue(ValidationIssue(
                    field=self.field_name,
                    message="Campos não permitidos encontrados no dicionário",
                    severity=ValidationSeverity.ERROR,
                    details={"extra_fields": extra_fields}
                ))
        
        # Validar cada campo conforme o schema
        for field, validator in self.schema.items():
            field_value = data.get(field)
            field_result = validator.validate(field_value)
            
            # Adicionar o nome do campo pai ao resultado
            for issue in field_result.issues:
                # Check if the field name already starts with the parent field to avoid duplication
                if not issue.field.startswith(f"{self.field_name}."):
                    # Only prefix with parent field name if not already present
                    if '.' in issue.field:
                        # For nested fields, extract the suffix after the first dot
                        suffix = issue.field.split('.', 1)[1]
                        issue.field = f"{self.field_name}.{suffix}"
                    else:
                        issue.field = f"{self.field_name}.{issue.field}"
                result.add_issue(issue)
        
        return result

class ListValidator(Validator[List[Any]]):
    """Validador para listas."""
    
    def __init__(
        self,
        field_name: str,
        item_validator: Optional[Validator[Any]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        required: bool = True,
        unique_items: bool = False
    ):
        """
        Inicializa o validador de listas.
        
        Args:
            field_name: Nome do campo sendo validado
            item_validator: Validador para os itens da lista (opcional)
            min_length: Tamanho mínimo da lista (opcional)
            max_length: Tamanho máximo da lista (opcional)
            required: Se a lista é obrigatória
            unique_items: Se os itens devem ser únicos
        """
        self.field_name = field_name
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
        self.required = required
        self.unique_items = unique_items
    
    def validate(self, data: Optional[List[Any]]) -> ValidationResult:
        """Valida uma lista."""
        result = ValidationResult()
        
        # Verificar se é None quando obrigatório
        if data is None:
            if self.required:
                result.add_issue(ValidationIssue(
                    field=self.field_name,
                    message="Lista obrigatória não fornecida",
                    severity=ValidationSeverity.ERROR
                ))
            return result
        
        # Verificar tamanho mínimo
        if self.min_length is not None and len(data) < self.min_length:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"Lista tem tamanho menor que o mínimo permitido ({self.min_length})",
                severity=ValidationSeverity.ERROR,
                details={"min_length": self.min_length, "actual_length": len(data)}
            ))
        
        # Verificar tamanho máximo
        if self.max_length is not None and len(data) > self.max_length:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"Lista excede o tamanho máximo permitido ({self.max_length})",
                severity=ValidationSeverity.ERROR,
                details={"max_length": self.max_length, "actual_length": len(data)}
            ))
        
        # Verificar unicidade dos itens
        if self.unique_items and len(data) != len(set(map(str, data))):
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="Lista contém itens duplicados",
                severity=ValidationSeverity.ERROR
            ))
        
        # Validar cada item se houver validador
        if self.item_validator:
            for i, item in enumerate(data):
                item_result = self.item_validator.validate(item)
                
                # Adicionar índice do item ao campo
                for issue in item_result.issues:
                    issue.field = f"{self.field_name}[{i}].{issue.field}"
                    result.add_issue(issue)
        
        return result

class DataFrameValidator(Validator[pd.DataFrame]):
    """Validador para DataFrames do pandas."""
    
    def __init__(
        self,
        field_name: str,
        column_validators: Dict[str, Validator[Any]],
        required_columns: Optional[List[str]] = None,
        min_rows: Optional[int] = None,
        max_rows: Optional[int] = None,
        allow_extra_columns: bool = False
    ):
        """
        Inicializa o validador de DataFrame.
        
        Args:
            field_name: Nome do campo sendo validado
            column_validators: Dicionário com validadores para cada coluna
            required_columns: Colunas que devem estar presentes
            min_rows: Número mínimo de linhas
            max_rows: Número máximo de linhas
            allow_extra_columns: Se permite colunas não definidas em column_validators
        """
        self.field_name = field_name
        self.column_validators = column_validators
        self.required_columns = required_columns or list(column_validators.keys())
        self.min_rows = min_rows
        self.max_rows = max_rows
        self.allow_extra_columns = allow_extra_columns
    
    def validate(self, data: pd.DataFrame) -> ValidationResult:
        """Valida um DataFrame."""
        result = ValidationResult()
        
        # Verificar colunas obrigatórias
        missing_columns = [col for col in self.required_columns if col not in data.columns]
        if missing_columns:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}",
                severity=ValidationSeverity.ERROR,
                details={"missing_columns": missing_columns}
            ))
        
        # Verificar colunas extras
        if not self.allow_extra_columns:
            extra_columns = [col for col in data.columns if col not in self.column_validators]
            if extra_columns:
                result.add_issue(ValidationIssue(
                    field=self.field_name,
                    message=f"Colunas não permitidas encontradas: {', '.join(extra_columns)}",
                    severity=ValidationSeverity.ERROR,
                    details={"extra_columns": extra_columns}
                ))
        
        # Verificar número de linhas
        if self.min_rows is not None and len(data) < self.min_rows:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"DataFrame tem menos linhas que o mínimo permitido ({self.min_rows})",
                severity=ValidationSeverity.ERROR,
                details={"min_rows": self.min_rows, "actual_rows": len(data)}
            ))
        
        if self.max_rows is not None and len(data) > self.max_rows:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message=f"DataFrame excede o número máximo de linhas permitido ({self.max_rows})",
                severity=ValidationSeverity.ERROR,
                details={"max_rows": self.max_rows, "actual_rows": len(data)}
            ))
        
        # Validar cada coluna com seu respectivo validador
        for col_name, validator in self.column_validators.items():
            if col_name in data.columns:
                for idx, value in enumerate(data[col_name]):
                    val_result = validator.validate(value)
                    
                    # Adicionar informações de linha/coluna aos problemas
                    for issue in val_result.issues:
                        issue.field = f"{self.field_name}[{idx}].{col_name}"
                        result.add_issue(issue)
        
        return result
