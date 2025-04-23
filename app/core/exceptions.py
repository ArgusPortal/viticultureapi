"""
Sistema centralizado de exceções.

Define exceções personalizadas para a aplicação, permitindo um tratamento
mais granular e específico de erros em diferentes componentes.
"""
from typing import Any, Dict, Optional, List, Type, Union
import traceback
import sys
import inspect
import logging

logger = logging.getLogger(__name__)

class BaseAppException(Exception):
    """Exceção base para todas as exceções da aplicação."""
    
    def __init__(
        self, 
        message: str = "Erro na aplicação", 
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.error_code = error_code
        self.original_exception = original_exception
        
        # Capturar informações adicionais sobre o erro
        self.traceback_info = self._get_traceback_info()
        self.caller_info = self._get_caller_info()
        
        # Registrar automaticamente o erro
        self._log_exception()
        
        super().__init__(message)
    
    def _get_traceback_info(self) -> str:
        """Obtém informações do traceback."""
        return traceback.format_exc()
    
    def _get_caller_info(self) -> Dict[str, Any]:
        """Obtém informações sobre quem chamou a exceção."""
        frame = inspect.currentframe()
        if frame:
            # Pular 2 frames (este método e __init__)
            caller_frame = inspect.getouterframes(frame)[2]
            return {
                "file": caller_frame.filename,
                "line": caller_frame.lineno,
                "function": caller_frame.function,
                "code": caller_frame.code_context[0].strip() if caller_frame.code_context else None
            }
        return {}
    
    def _log_exception(self) -> None:
        """Registra a exceção no sistema de log."""
        log_message = f"{self.__class__.__name__}: {self.message}"
        
        if self.original_exception:
            log_message += f" | Original exception: {str(self.original_exception)}"
        
        if self.error_code:
            log_message += f" | Error code: {self.error_code}"
        
        # Incluir informações do caller
        caller_info = f"{self.caller_info.get('file', 'unknown')}:{self.caller_info.get('line', 'unknown')}"
        log_message += f" | Called from: {caller_info}"
        
        # Usar o nível de log apropriado com base no status code
        if self.status_code >= 500:
            logger.error(log_message)
            # Registrar traceback completo apenas para erros 5xx
            logger.debug(f"Traceback:\n{self.traceback_info}")
        elif self.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a exceção para um dicionário."""
        result = {
            "message": self.message,
            "status_code": self.status_code,
        }
        
        if self.error_code:
            result["error_code"] = self.error_code
            
        if self.details:
            result["details"] = self.details
        
        return result

# Exceções HTTP (4xx)
class HTTPException(BaseAppException):
    """Base para exceções HTTP."""
    pass

class BadRequestException(HTTPException):
    """Erro 400 - Bad Request."""
    
    def __init__(
        self, 
        message: str = "Requisição inválida", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=400,
            error_code=error_code or "BAD_REQUEST",
            original_exception=original_exception
        )

class UnauthorizedException(HTTPException):
    """Erro 401 - Unauthorized."""
    
    def __init__(
        self, 
        message: str = "Não autorizado", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=401,
            error_code=error_code or "UNAUTHORIZED",
            original_exception=original_exception
        )

class ForbiddenException(HTTPException):
    """Erro 403 - Forbidden."""
    
    def __init__(
        self, 
        message: str = "Acesso proibido", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=403,
            error_code=error_code or "FORBIDDEN",
            original_exception=original_exception
        )

class NotFoundException(HTTPException):
    """Erro 404 - Not Found."""
    
    def __init__(
        self, 
        message: str = "Recurso não encontrado", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=404,
            error_code=error_code or "NOT_FOUND",
            original_exception=original_exception
        )

class ConflictException(HTTPException):
    """Erro 409 - Conflict."""
    
    def __init__(
        self, 
        message: str = "Conflito de recursos", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=409,
            error_code=error_code or "CONFLICT",
            original_exception=original_exception
        )

class TooManyRequestsException(HTTPException):
    """Erro 429 - Too Many Requests."""
    
    def __init__(
        self, 
        message: str = "Muitas requisições", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        retry_after: Optional[int] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            details=details,
            status_code=429,
            error_code=error_code or "TOO_MANY_REQUESTS",
            original_exception=original_exception
        )

# Exceções de Servidor (5xx)
class InternalServerException(BaseAppException):
    """Erro 500 - Internal Server Error."""
    
    def __init__(
        self, 
        message: str = "Erro interno do servidor", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=500,
            error_code=error_code or "INTERNAL_SERVER_ERROR",
            original_exception=original_exception
        )

class ServiceUnavailableException(BaseAppException):
    """Erro 503 - Service Unavailable."""
    
    def __init__(
        self, 
        message: str = "Serviço indisponível", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=503,
            error_code=error_code or "SERVICE_UNAVAILABLE",
            original_exception=original_exception
        )

# Exceções de Domínio (específicas da aplicação)
class DomainException(BaseAppException):
    """Base para exceções de domínio."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=status_code,
            error_code=error_code,
            original_exception=original_exception
        )

class ScraperException(DomainException):
    """Exceção para erros de scraping."""
    
    def __init__(
        self, 
        message: str = "Erro ao fazer scraping dos dados", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        fallback_attempted: bool = False
    ):
        details = details or {}
        details["fallback_attempted"] = fallback_attempted
        
        super().__init__(
            message=message,
            details=details,
            status_code=503 if not fallback_attempted else 500,
            error_code=error_code or "SCRAPER_ERROR",
            original_exception=original_exception
        )

class DataProcessingException(DomainException):
    """Exceção para erros de processamento de dados."""
    
    def __init__(
        self, 
        message: str = "Erro ao processar dados", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=500,
            error_code=error_code or "DATA_PROCESSING_ERROR",
            original_exception=original_exception
        )

class ValidationException(DomainException):
    """Exceção para erros de validação."""
    
    def __init__(
        self, 
        message: str = "Erro de validação", 
        details: Optional[Dict[str, Any]] = None,
        field_errors: Optional[Dict[str, List[str]]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = details or {}
        if field_errors:
            details["field_errors"] = field_errors
            
        super().__init__(
            message=message,
            details=details,
            status_code=400,
            error_code=error_code or "VALIDATION_ERROR",
            original_exception=original_exception
        )

# Exceções de Infraestrutura
class InfrastructureException(BaseAppException):
    """Base para exceções de infraestrutura."""
    pass

class DatabaseException(InfrastructureException):
    """Exceção para erros de banco de dados."""
    
    def __init__(
        self, 
        message: str = "Erro de banco de dados", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            details=details,
            status_code=500,
            error_code=error_code or "DATABASE_ERROR",
            original_exception=original_exception
        )

class CacheException(InfrastructureException):
    """Exceção para erros de cache."""
    
    def __init__(
        self, 
        message: str = "Erro no sistema de cache", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        cache_key: Optional[str] = None,
        provider: Optional[str] = None
    ):
        details = details or {}
        if cache_key:
            details["cache_key"] = cache_key
        if provider:
            details["provider"] = provider
            
        super().__init__(
            message=message,
            details=details,
            status_code=500,
            error_code=error_code or "CACHE_ERROR",
            original_exception=original_exception
        )

class ExternalServiceException(InfrastructureException):
    """Exceção para erros em serviços externos."""
    
    def __init__(
        self, 
        message: str = "Erro em serviço externo", 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None,
        status_code_from_service: Optional[int] = None
    ):
        details = details or {}
        if service_name:
            details["service_name"] = service_name
        if status_code_from_service:
            details["status_code_from_service"] = status_code_from_service
            
        super().__init__(
            message=message,
            details=details,
            status_code=502,  # Bad Gateway
            error_code=error_code or "EXTERNAL_SERVICE_ERROR",
            original_exception=original_exception
        )

# Handler para converter exceções padrão em exceções da aplicação
def handle_exception(exception: Exception) -> BaseAppException:
    """
    Converte exceções padrão em exceções da aplicação.
    
    Args:
        exception: Exceção a ser convertida
        
    Returns:
        Exceção da aplicação
    """
    if isinstance(exception, BaseAppException):
        return exception
    
    # Mapear exceções comuns para exceções da aplicação
    if isinstance(exception, ValueError):
        return ValidationException(
            message=str(exception) or "Valor inválido",
            original_exception=exception
        )
    
    if isinstance(exception, KeyError):
        return NotFoundException(
            message=f"Chave não encontrada: {str(exception)}",
            original_exception=exception
        )
    
    if isinstance(exception, FileNotFoundError):
        return NotFoundException(
            message=f"Arquivo não encontrado: {str(exception)}",
            original_exception=exception
        )
    
    if isinstance(exception, PermissionError):
        return ForbiddenException(
            message=f"Permissão negada: {str(exception)}",
            original_exception=exception
        )
    
    if isinstance(exception, TimeoutError):
        return ServiceUnavailableException(
            message=f"Tempo limite excedido: {str(exception)}",
            original_exception=exception
        )
    
    # Exceção genérica para outros casos
    return InternalServerException(
        message=str(exception) or "Erro interno",
        original_exception=exception
    )
