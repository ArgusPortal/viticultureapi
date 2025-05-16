"""
Integração do sistema de validação com o pipeline de dados.

Fornece transformadores que incluem validação e normalização.
"""
import pandas as pd
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, TypeVar, Generic, cast, Type, Callable

from app.core.pipeline import Transformer
from app.core.validation.interface import (
    Validator, Normalizer, ValidationResult, ValidatingTransformer
)
from app.core.validation.reporter import ValidationReporter

# Tipos genéricos para entrada e saída
T = TypeVar('T')
U = TypeVar('U')

class ValidatingPipelineTransformer(Transformer[T, U], ValidatingTransformer[T, U]):
    """
    Transformador para pipeline com validação integrada.
    
    Permite integrar validação a transformadores existentes.
    """
    
    def __init__(
        self, 
        name: str,
        validator: Validator[T],
        transform_func: Optional[Callable[[T], U]] = None,  # Changed callable to Callable
        fail_on_invalid: bool = False,
        report_path: Optional[str] = None
    ):
        """
        Inicializa o transformador com validação.
        
        Args:
            name: Nome do transformador
            validator: Validador a ser aplicado aos dados
            transform_func: Função de transformação (opcional)
            fail_on_invalid: Se deve falhar em caso de dados inválidos
            report_path: Caminho para salvar relatórios de validação
        """
        self.name = name
        self.validator = validator
        self.transform_func = transform_func
        self.fail_on_invalid = fail_on_invalid
        self.report_path = report_path
        self.reporter = ValidationReporter(name)
        self.logger = logging.getLogger(f"transformer.validating.{name}")
    
    def transform(self, data: T) -> U:
        """
        Transforma os dados após validação.
        
        Args:
            data: Dados a serem transformados
            
        Returns:
            Dados transformados
            
        Raises:
            ValueError: Se os dados são inválidos e fail_on_invalid=True
        """
        transformed_data, validation_result = self.transform_and_validate(data)
        return transformed_data
    
    def transform_and_validate(self, data: T) -> Tuple[U, ValidationResult]:
        """
        Transforma e valida os dados.
        
        Args:
            data: Dados a serem transformados e validados
            
        Returns:
            Tuple com dados transformados e resultado da validação
            
        Raises:
            ValueError: Se os dados são inválidos e fail_on_invalid=True
        """
        # Validar os dados
        validation_result = self.validator.validate(data)
        
        # Salvar relatório se especificado
        if self.report_path:
            self.reporter.to_json(validation_result, self.report_path)
        
        # Registrar problemas no log
        if not validation_result.is_valid:
            self.logger.warning(f"Validation found {len(validation_result.issues)} issues")
            for issue in validation_result.issues:
                level = logging.WARNING if issue.severity.value in ('warning', 'info') else logging.ERROR
                self.logger.log(level, f"{issue.field}: {issue.message}")
        
        # Falhar se necessário
        if self.fail_on_invalid and not validation_result.is_valid:
            error_msg = f"Validation failed with {len(validation_result.issues)} issues"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Aplicar transformação se fornecida
        if self.transform_func:
            transformed_data = self.transform_func(data)
        else:
            # Se não há transformação, converter para o tipo de saída esperado
            transformed_data = cast(U, data)
        
        return transformed_data, validation_result


class NormalizingPipelineTransformer(Transformer[T, U]):
    """
    Transformador para pipeline com normalização integrada.
    
    Permite aplicar normalização de dados dentro de um pipeline.
    """
    
    def __init__(
        self,
        name: str,
        normalizer: Normalizer[T, U],
        fail_on_invalid: bool = False,
        report_path: Optional[str] = None
    ):
        """
        Inicializa o transformador com normalização.
        
        Args:
            name: Nome do transformador
            normalizer: Normalizador a ser aplicado aos dados
            fail_on_invalid: Se deve falhar em caso de dados inválidos
            report_path: Caminho para salvar relatórios de validação
        """
        self.name = name
        self.normalizer = normalizer
        self.fail_on_invalid = fail_on_invalid
        self.report_path = report_path
        self.reporter = ValidationReporter(name)
        self.logger = logging.getLogger(f"transformer.normalizing.{name}")
    
    def transform(self, data: T) -> U:
        """
        Normaliza os dados.
        
        Args:
            data: Dados a serem normalizados
            
        Returns:
            Dados normalizados
            
        Raises:
            ValueError: Se os dados são inválidos após normalização e fail_on_invalid=True
        """
        # Normalizar os dados
        normalized_data, validation_result = self.normalizer.normalize(data)
        
        # Salvar relatório se especificado
        if self.report_path:
            self.reporter.to_json(validation_result, self.report_path)
        
        # Registrar problemas no log
        if not validation_result.is_valid:
            self.logger.warning(f"Normalization found {len(validation_result.issues)} issues")
            for issue in validation_result.issues:
                level = logging.WARNING if issue.severity.value in ('warning', 'info') else logging.ERROR
                self.logger.log(level, f"{issue.field}: {issue.message}")
        
        # Falhar se necessário
        if self.fail_on_invalid and not validation_result.is_valid:
            error_msg = f"Normalization failed with {len(validation_result.issues)} issues"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        return normalized_data


class ValidatingDataFrameTransformer(Transformer[pd.DataFrame, pd.DataFrame]):
    """
    Transformador específico para validação de DataFrames.
    
    Permite validar um DataFrame e opcionalmente aplicar transformações.
    """
    
    def __init__(
        self,
        name: str,
        column_validators: Dict[str, Validator[Any]],
        required_columns: Optional[List[str]] = None,
        min_rows: Optional[int] = None,
        max_rows: Optional[int] = None,
        allow_extra_columns: bool = False,
        transform_func: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,  # Changed callable to Callable
        fail_on_invalid: bool = False,
        report_path: Optional[str] = None
    ):
        """
        Inicializa o transformador para validação de DataFrame.
        
        Args:
            name: Nome do transformador
            column_validators: Dicionário de validadores por coluna
            required_columns: Colunas obrigatórias (opcional)
            min_rows: Número mínimo de linhas (opcional)
            max_rows: Número máximo de linhas (opcional)
            allow_extra_columns: Se permite colunas extras
            transform_func: Função de transformação adicional (opcional)
            fail_on_invalid: Se deve falhar em caso de dados inválidos
            report_path: Caminho para salvar relatórios de validação
        """
        from app.core.validation.validators import DataFrameValidator
        
        self.name = name
        self.validator = DataFrameValidator(
            field_name=name,
            column_validators=column_validators,
            required_columns=required_columns,
            min_rows=min_rows,
            max_rows=max_rows,
            allow_extra_columns=allow_extra_columns
        )
        self.transform_func = transform_func
        self.fail_on_invalid = fail_on_invalid
        self.report_path = report_path
        self.reporter = ValidationReporter(name)
        self.logger = logging.getLogger(f"transformer.validating_df.{name}")
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Valida e opcionalmente transforma um DataFrame.
        
        Args:
            data: DataFrame a ser validado e transformado
            
        Returns:
            DataFrame validado e transformado
            
        Raises:
            ValueError: Se os dados são inválidos e fail_on_invalid=True
        """
        # Validar o DataFrame
        validation_result = self.validator.validate(data)
        
        # Salvar relatório se especificado
        if self.report_path:
            self.reporter.to_json(validation_result, self.report_path)
        
        # Registrar problemas no log
        if not validation_result.is_valid:
            self.logger.warning(f"DataFrame validation found {len(validation_result.issues)} issues")
            for issue in validation_result.issues:
                level = logging.WARNING if issue.severity.value in ('warning', 'info') else logging.ERROR
                self.logger.log(level, f"{issue.field}: {issue.message}")
        
        # Falhar se necessário
        if self.fail_on_invalid and not validation_result.is_valid:
            error_msg = f"DataFrame validation failed with {len(validation_result.issues)} issues"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Aplicar transformação se fornecida
        if self.transform_func:
            return self.transform_func(data)
        
        return data


class NormalizingDataFrameTransformer(Transformer[pd.DataFrame, pd.DataFrame]):
    """
    Transformador específico para normalização de DataFrames.
    
    Permite normalizar colunas de um DataFrame.
    """
    
    def __init__(
        self,
        name: str,
        column_normalizers: Dict[str, Normalizer[Any, Any]],
        fail_on_invalid: bool = False,
        report_path: Optional[str] = None
    ):
        """
        Inicializa o transformador para normalização de DataFrame.
        
        Args:
            name: Nome do transformador
            column_normalizers: Dicionário de normalizadores por coluna
            fail_on_invalid: Se deve falhar em caso de dados inválidos
            report_path: Caminho para salvar relatórios de validação
        """
        from app.core.validation.normalizer import DataFrameColumnNormalizer
        
        self.name = name
        self.normalizer = DataFrameColumnNormalizer(column_normalizers)
        self.fail_on_invalid = fail_on_invalid
        self.report_path = report_path
        self.reporter = ValidationReporter(name)
        self.logger = logging.getLogger(f"transformer.normalizing_df.{name}")
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza as colunas de um DataFrame.
        
        Args:
            data: DataFrame a ser normalizado
            
        Returns:
            DataFrame normalizado
            
        Raises:
            ValueError: Se os dados são inválidos após normalização e fail_on_invalid=True
        """
        from app.core.validation.interface import ValidationResult
        
        # Normalizar o DataFrame
        normalized_df, issues_by_column = self.normalizer.normalize_dataframe(data)
        
        # Criar resultado de validação consolidado
        validation_result = ValidationResult()
        for column, issues in issues_by_column.items():
            validation_result.add_issues(issues)
        
        # Salvar relatório se especificado
        if self.report_path:
            self.reporter.to_json(validation_result, self.report_path)
        
        # Registrar problemas no log
        if validation_result.has_issues():
            self.logger.warning(f"DataFrame normalization found {len(validation_result.issues)} issues")
            for issue in validation_result.issues:
                level = logging.WARNING if issue.severity.value in ('warning', 'info') else logging.ERROR
                self.logger.log(level, f"{issue.field}: {issue.message}")
        
        # Falhar se necessário
        if self.fail_on_invalid and not validation_result.is_valid:
            error_msg = f"DataFrame normalization failed with {len(validation_result.issues)} issues"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        return normalized_df


class ValidationPipelineFactory:
    """
    Fábrica para criar pipelines com validação e normalização.
    
    Simplifica a criação de componentes comuns de validação para pipelines.
    """
    
    @staticmethod
    def create_validating_transformer(
        name: str,
        validator: Validator[T],
        transform_func: Optional[Callable[[T], U]] = None,  # Changed callable to Callable
        fail_on_invalid: bool = False,
        report_dir: Optional[str] = None
    ) -> ValidatingPipelineTransformer[T, U]:
        """
        Cria um transformador com validação.
        
        Args:
            name: Nome do transformador
            validator: Validador a ser utilizado
            transform_func: Função de transformação opcional
            fail_on_invalid: Se deve falhar em caso de dados inválidos
            report_dir: Diretório para relatórios (opcional)
            
        Returns:
            Transformador com validação configurado
        """
        import os
        
        report_path = None
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
            report_path = os.path.join(report_dir, f"{name}_validation.json")
        
        return ValidatingPipelineTransformer(
            name=name,
            validator=validator,
            transform_func=transform_func,
            fail_on_invalid=fail_on_invalid,
            report_path=report_path
        )
    
    @staticmethod
    def create_normalizing_transformer(
        name: str,
        normalizer: Normalizer[T, U],
        fail_on_invalid: bool = False,
        report_dir: Optional[str] = None
    ) -> NormalizingPipelineTransformer[T, U]:
        """
        Cria um transformador com normalização.
        
        Args:
            name: Nome do transformador
            normalizer: Normalizador a ser utilizado
            fail_on_invalid: Se deve falhar em caso de dados inválidos
            report_dir: Diretório para relatórios (opcional)
            
        Returns:
            Transformador com normalização configurado
        """
        import os
        
        report_path = None
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
            report_path = os.path.join(report_dir, f"{name}_normalization.json")
        
        return NormalizingPipelineTransformer(
            name=name,
            normalizer=normalizer,
            fail_on_invalid=fail_on_invalid,
            report_path=report_path
        )
    
    @staticmethod
    def create_validating_dataframe_transformer(
        name: str,
        column_validators: Dict[str, Validator[Any]],
        required_columns: Optional[List[str]] = None,
        min_rows: Optional[int] = None,
        max_rows: Optional[int] = None,
        allow_extra_columns: bool = False,
        transform_func: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,  # Changed callable to Callable
        fail_on_invalid: bool = False,
        report_dir: Optional[str] = None
    ) -> ValidatingDataFrameTransformer:
        """
        Cria um transformador para validação de DataFrame.
        
        Args:
            name: Nome do transformador
            column_validators: Validadores por coluna
            required_columns: Colunas obrigatórias
            min_rows: Número mínimo de linhas
            max_rows: Número máximo de linhas
            allow_extra_columns: Se permite colunas extras
            transform_func: Função de transformação adicional
            fail_on_invalid: Se deve falhar em caso de dados inválidos
            report_dir: Diretório para relatórios
            
        Returns:
            Transformador para validação de DataFrame
        """
        import os
        
        report_path = None
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
            report_path = os.path.join(report_dir, f"{name}_df_validation.json")
        
        return ValidatingDataFrameTransformer(
            name=name,
            column_validators=column_validators,
            required_columns=required_columns,
            min_rows=min_rows,
            max_rows=max_rows,
            allow_extra_columns=allow_extra_columns,
            transform_func=transform_func,
            fail_on_invalid=fail_on_invalid,
            report_path=report_path
        )
    
    @staticmethod
    def create_normalizing_dataframe_transformer(
        name: str,
        column_normalizers: Dict[str, Normalizer[Any, Any]],
        fail_on_invalid: bool = False,
        report_dir: Optional[str] = None
    ) -> NormalizingDataFrameTransformer:
        """
        Cria um transformador para normalização de DataFrame.
        
        Args:
            name: Nome do transformador
            column_normalizers: Normalizadores por coluna
            fail_on_invalid: Se deve falhar em caso de dados inválidos
            report_dir: Diretório para relatórios
            
        Returns:
            Transformador para normalização de DataFrame
        """
        import os
        
        report_path = None
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
            report_path = os.path.join(report_dir, f"{name}_df_normalization.json")
        
        return NormalizingDataFrameTransformer(
            name=name,
            column_normalizers=column_normalizers,
            fail_on_invalid=fail_on_invalid,
            report_path=report_path
        )
