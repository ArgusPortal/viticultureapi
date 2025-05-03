"""
Interfaces para validação de dados.

Define as interfaces abstratas para validação e normalização de dados.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

# Tipo genérico para dados de entrada
T = TypeVar('T')
# Tipo genérico para dados de saída (dados normalizados)
U = TypeVar('U')

class ValidationSeverity(Enum):
    """Níveis de severidade para problemas de validação."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationIssue:
    """Representa um problema encontrado durante a validação."""
    
    def __init__(
        self,
        field: str,
        message: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        value: Any = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa um problema de validação.
        
        Args:
            field: Campo ou atributo com problema
            message: Descrição do problema
            severity: Severidade do problema
            value: Valor problemático (opcional)
            code: Código de identificação do problema (opcional)
            details: Detalhes adicionais sobre o problema (opcional)
        """
        self.field = field
        self.message = message
        self.severity = severity
        self.value = value
        self.code = code or self._generate_code()
        self.details = details or {}
        
    def _generate_code(self) -> str:
        """Gera um código baseado no campo e na mensagem."""
        import hashlib
        hash_input = f"{self.field}:{self.message}"
        return f"VAL-{hashlib.md5(hash_input.encode()).hexdigest()[:6]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o problema para um dicionário."""
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "code": self.code,
            "details": self.details
        }
    
    def __str__(self) -> str:
        return f"{self.severity.value.upper()}: {self.field} - {self.message}"

class ValidationResult:
    """Resultado de uma validação, contendo problemas encontrados."""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self._fields_with_issues: Set[str] = set()
        
    def add_issue(self, issue: ValidationIssue) -> None:
        """Adiciona um problema ao resultado."""
        self.issues.append(issue)
        self._fields_with_issues.add(issue.field)
        
    def add_issues(self, issues: List[ValidationIssue]) -> None:
        """Adiciona múltiplos problemas ao resultado."""
        for issue in issues:
            self.add_issue(issue)
            
    def has_issues(self, severity: Optional[ValidationSeverity] = None) -> bool:
        """
        Verifica se existem problemas.
        
        Args:
            severity: Se fornecido, verifica apenas problemas com esta severidade
            
        Returns:
            True se existirem problemas (da severidade específica, se informada)
        """
        if severity is None:
            return len(self.issues) > 0
        return any(issue.severity == severity for issue in self.issues)
    
    def has_field_issues(self, field: str) -> bool:
        """Verifica se um campo específico tem problemas."""
        return field in self._fields_with_issues
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Retorna problemas com a severidade especificada."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_field(self, field: str) -> List[ValidationIssue]:
        """Retorna problemas para o campo especificado."""
        return [issue for issue in self.issues if issue.field == field]
    
    def merge(self, other: 'ValidationResult') -> None:
        """Mescla outro resultado de validação com este."""
        self.add_issues(other.issues)
    
    @property
    def is_valid(self) -> bool:
        """Verifica se não há problemas de severidade ERROR ou CRITICAL."""
        return not any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            for issue in self.issues
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o resultado para um dicionário."""
        return {
            "is_valid": self.is_valid,
            "total_issues": len(self.issues),
            "issues": [issue.to_dict() for issue in self.issues]
        }
        
    def __bool__(self) -> bool:
        return self.is_valid

class Validator(Generic[T], ABC):
    """Interface abstrata para validadores."""
    
    @abstractmethod
    def validate(self, data: T) -> ValidationResult:
        """
        Valida os dados fornecidos.
        
        Args:
            data: Dados a serem validados
            
        Returns:
            Resultado da validação
        """
        pass

class Normalizer(Generic[T, U], ABC):
    """Interface abstrata para normalizadores de dados."""
    
    @abstractmethod
    def normalize(self, data: T) -> Tuple[U, ValidationResult]:
        """
        Normaliza os dados fornecidos.
        
        Args:
            data: Dados a serem normalizados
            
        Returns:
            Tuple contendo os dados normalizados e o resultado da validação
        """
        pass

class ValidatingTransformer(Generic[T, U], ABC):
    """
    Interface para transformadores que validam dados.
    
    Combina validação e transformação em uma única operação.
    """
    
    @abstractmethod
    def transform_and_validate(self, data: T) -> Tuple[U, ValidationResult]:
        """
        Transforma e valida os dados.
        
        Args:
            data: Dados a serem transformados e validados
            
        Returns:
            Tuple contendo os dados transformados e o resultado da validação
        """
        pass
