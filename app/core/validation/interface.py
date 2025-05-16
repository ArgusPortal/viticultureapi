"""
Interfaces do sistema de validação.

Este módulo define as interfaces fundamentais e classes base para o sistema
de validação de dados, incluindo os conceitos de validador, resultado de validação,
normalizador e transformador com validação integrada.

Classes:
    ValidationSeverity: Enum para níveis de severidade de problemas
    ValidationIssue: Representa um problema encontrado na validação
    ValidationResult: Agrega os problemas encontrados durante uma validação
    Validator: Interface base para validadores
    Normalizer: Interface para normalizadores de dados
    ValidatingTransformer: Interface para transformadores com validação
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, Union

# Tipos genéricos para dados de entrada/saída
T = TypeVar('T')
U = TypeVar('U')

class ValidationSeverity(Enum):
    """
    Níveis de severidade para problemas de validação.
    
    Attributes:
        INFO: Informação não crítica, apenas aviso informativo
        WARNING: Aviso, problema não crítico mas relevante
        ERROR: Erro, problema crítico que impede validação
        CRITICAL: Erro grave, problema que pode comprometer integridade dos dados
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationIssue:
    """
    Representa um problema identificado durante validação.
    
    Um problema pode ser desde um simples aviso informativo até
    um erro crítico que invalida completamente os dados.
    
    Attributes:
        field: Nome do campo onde o problema foi encontrado
        message: Mensagem descritiva do problema
        severity: Nível de severidade do problema
        value: Valor que causou o problema (opcional)
        code: Código único do problema (opcional)
        details: Detalhes adicionais sobre o problema (opcional)
    """
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
            field: Nome do campo onde o problema foi encontrado
            message: Mensagem descritiva do problema
            severity: Nível de severidade do problema
            value: Valor que causou o problema (opcional)
            code: Código único do problema (opcional)
            details: Detalhes adicionais sobre o problema (opcional)
        """
        self.field = field
        self.message = message
        self.severity = severity
        self.value = value
        self.code = code or self._generate_code()
        self.details = details or {}
        
    def _generate_code(self) -> str:
        """
        Gera um código único para o problema baseado em seus atributos.
        
        Returns:
            Código alfanumérico único para o problema
        """
        import hashlib
        
        # Usar um hash dos atributos para gerar um código único
        base_string = f"{self.field}:{self.message}:{self.severity.value}"
        if self.value is not None:
            base_string += f":{str(self.value)}"
            
        return f"VAL-{hashlib.md5(base_string.encode()).hexdigest()[:6]}"
        
    def __str__(self) -> str:
        """
        Representação de string do problema de validação.
        
        Returns:
            Descrição legível do problema
        """
        return f"{self.severity.value.upper()}: {self.field} - {self.message}"
        
    def to_dict(self) -> Dict[str, Any]:  # Updated return type to be more accurate
        """
        Converte o problema para um dicionário.
        
        Returns:
            Representação em dicionário do problema
        """
        result: Dict[str, Any] = {  # Explicitly annotate result as Dict[str, Any]
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "code": self.code
        }
        
        # Adicionar value somente se não for None
        if self.value is not None:
            result["value"] = self.value
            
        # Adicionar details somente se não estiver vazio
        if self.details:
            result["details"] = self.details
            
        return result

class ValidationResult:
    """
    Agrega problemas encontrados durante uma validação.
    
    Mantém uma lista de problemas (ValidationIssue) e fornece métodos
    para verificar se a validação passou, filtrar problemas por severidade
    ou campo, e combinar resultados de múltiplas validações.
    
    Attributes:
        issues: Lista de problemas encontrados na validação
    """
    def __init__(self):
        """
        Inicializa um resultado de validação vazio.
        """
        self.issues: List[ValidationIssue] = []
    
    def add_issue(self, issue: ValidationIssue) -> None:
        """
        Adiciona um problema ao resultado da validação.
        
        Args:
            issue: Problema a ser adicionado
        """
        self.issues.append(issue)
    
    def add_issues(self, issues: List[ValidationIssue]) -> None:
        """
        Adiciona múltiplos problemas ao resultado da validação.
        
        Args:
            issues: Lista de problemas a serem adicionados
        """
        for issue in issues:
            self.add_issue(issue)
    
    def has_issues(self, severity: Optional[ValidationSeverity] = None) -> bool:
        """
        Verifica se há problemas de uma severidade específica.
        
        Args:
            severity: Severidade dos problemas a serem verificados.
                     Se None, verifica todos os problemas.
        
        Returns:
            True se há problemas da severidade especificada, False caso contrário
        """
        if severity is None:
            return len(self.issues) > 0
            
        return any(issue.severity == severity for issue in self.issues)
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """
        Filtra problemas por severidade.
        
        Args:
            severity: Severidade dos problemas a serem retornados
            
        Returns:
            Lista de problemas com a severidade especificada
        """
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_field(self, field: str) -> List[ValidationIssue]:
        """
        Filtra problemas por campo.
        
        Args:
            field: Nome do campo para filtrar problemas
            
        Returns:
            Lista de problemas associados ao campo especificado
        """
        return [issue for issue in self.issues if issue.field == field]
    
    @property
    def is_valid(self) -> bool:
        """
        Verifica se não há erros críticos no resultado.
        
        Um resultado é considerado válido se não contém problemas
        com severidade ERROR ou CRITICAL.
        
        Returns:
            True se o resultado é válido, False caso contrário
        """
        return not any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL) 
            for issue in self.issues
        )
    
    def merge(self, other: 'ValidationResult') -> None:
        """
        Combina este resultado com outro resultado de validação.
        
        Args:
            other: Outro resultado de validação a ser combinado
        """
        self.add_issues(other.issues)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o resultado para um dicionário.
        
        Returns:
            Representação em dicionário do resultado de validação
        """
        return {
            "is_valid": self.is_valid,
            "total_issues": len(self.issues),
            "issues": [issue.to_dict() for issue in self.issues]
        }

def validate_common(
    value: Any,
    field_name: str,
    required: bool = True,
    validation_result: Optional[ValidationResult] = None
) -> Tuple[ValidationResult, bool]:
    """
    Realiza validações comuns a todos os tipos de validadores.
    
    Args:
        value: Valor a ser validado
        field_name: Nome do campo sendo validado
        required: Se o valor é obrigatório
        validation_result: Resultado de validação existente (opcional)
        
    Returns:
        Tupla (resultado_validacao, deve_continuar_validacao)
        - resultado_validacao: ValidationResult atualizado
        - deve_continuar_validacao: Se deve continuar com validações específicas
    """
    result = validation_result or ValidationResult()
    
    # Verificar se é None quando obrigatório
    if value is None:
        if required:
            result.add_issue(ValidationIssue(
                field=field_name,
                message="Campo obrigatório não fornecido",
                severity=ValidationSeverity.ERROR
            ))
        return result, False  # Não continue com validações específicas
    
    return result, True  # Continue com validações específicas

class Validator(Generic[T], ABC):
    """
    Interface base para validadores.
    
    Um validador é responsável por verificar se dados de um tipo específico
    atendem a um conjunto de regras e produzir um resultado de validação
    estruturado indicando problemas encontrados.
    
    Type Parameters:
        T: Tipo de dados que este validador pode validar
    """
    @abstractmethod
    def validate(self, data: T) -> ValidationResult:
        """
        Valida dados de um tipo específico.
        
        Args:
            data: Dados a serem validados
            
        Returns:
            Resultado da validação contendo problemas encontrados
        """
        pass

class Normalizer(Generic[T, U], ABC):
    """
    Interface para normalizadores de dados.
    
    Um normalizador é responsável por converter dados de um formato para outro,
    aplicando validações no processo e retornando tanto o dado normalizado
    quanto o resultado da validação.
    
    Type Parameters:
        T: Tipo de entrada do normalizador
        U: Tipo de saída do normalizador
    """
    @abstractmethod
    def normalize(self, data: T) -> Tuple[U, ValidationResult]:
        """
        Normaliza dados de um tipo para outro, validando no processo.
        
        Args:
            data: Dados a serem normalizados
            
        Returns:
            Tupla contendo dados normalizados e resultado da validação
        """
        pass

class ValidatingTransformer(Generic[T, U], ABC):
    """
    Interface para transformadores com validação integrada.
    
    Um transformador com validação converte dados de um formato para outro,
    realizando validações no processo e retornando tanto o resultado da
    transformação quanto o resultado da validação.
    
    Type Parameters:
        T: Tipo de entrada do transformador
        U: Tipo de saída do transformador
    """
    @abstractmethod
    def transform_and_validate(self, data: T) -> Tuple[U, ValidationResult]:
        """
        Transforma e valida dados.
        
        Args:
            data: Dados a serem transformados e validados
            
        Returns:
            Tupla com dados transformados e resultado da validação
        """
        pass
