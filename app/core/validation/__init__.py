"""
Sistema de validação de dados.

Fornece interfaces e implementações para validação de dados.
"""
from app.core.validation.interface import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    Validator,
    Normalizer,
    ValidatingTransformer,
    validate_common
)

from app.core.validation.validators import (
    StringValidator,
    NumericValidator,
    DateValidator,
    DictValidator,
    ListValidator,
    DataFrameValidator
)

from app.core.validation.normalizer import (
    StringNormalizer,
    NumericNormalizer,
    DateNormalizer,
    DictNormalizer,
    DataFrameColumnNormalizer
)

from app.core.validation.reporter import (
    ValidationReporter,
    DataQualityMonitor
)

from app.core.validation.pipeline import (
    ValidatingPipelineTransformer,
    NormalizingPipelineTransformer,
    ValidatingDataFrameTransformer,
    NormalizingDataFrameTransformer,
    ValidationPipelineFactory
)

from app.core.validation.schema import (
    ValidationSchemas,
    create_validator_from_schema
)

__all__ = [
    # Interfaces
    'ValidationSeverity',
    'ValidationIssue',
    'ValidationResult',
    'Validator',
    'Normalizer',
    'ValidatingTransformer',
    'validate_common',  # Adicionar a nova função utilitária
    
    # Validators
    'StringValidator',
    'NumericValidator',
    'DateValidator',
    'DictValidator',
    'ListValidator',
    'DataFrameValidator',
    
    # Normalizers
    'StringNormalizer',
    'NumericNormalizer',
    'DateNormalizer',
    'DictNormalizer',
    'DataFrameColumnNormalizer',
    
    # Reporters
    'ValidationReporter',
    'DataQualityMonitor',
    
    # Pipeline Integration
    'ValidatingPipelineTransformer',
    'NormalizingPipelineTransformer',
    'ValidatingDataFrameTransformer',
    'NormalizingDataFrameTransformer',
    'ValidationPipelineFactory',
    
    # Schema
    'ValidationSchemas',
    'create_validator_from_schema'
]
