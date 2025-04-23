"""
Sistema de logging centralizado.

Fornece funções para configurar e utilizar o sistema de logging
de forma consistente em toda a aplicação.
"""
import logging
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

# Formatar mensagens de log como JSON
class JsonFormatter(logging.Formatter):
    """
    Formatter para logs em formato JSON.
    
    Formata as mensagens de log como objetos JSON estruturados,
    facilitando a análise por ferramentas de logging.
    """
    
    def __init__(self, include_timestamp: bool = True, app_name: str = "viticultureapi"):
        """
        Inicializa o formatter.
        
        Args:
            include_timestamp: Se True, inclui timestamp no log
            app_name: Nome da aplicação para incluir nos logs
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.app_name = app_name
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o registro de log.
        
        Args:
            record: Registro de log
            
        Returns:
            Mensagem formatada
        """
        # Usar a anotação correta para permitir qualquer tipo de valor no dicionário
        log_data: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "app": self.app_name
        }
        
        # Adicionar timestamp
        if self.include_timestamp:
            log_data["timestamp"] = datetime.fromtimestamp(record.created).isoformat()
        
        # Adicionar informações de arquivo e linha
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }
        
        # Adicionar exceção se disponível
        if record.exc_info:
            try:
                # Verificar se não estamos tentando acessar atributos em None
                if record.exc_info[0] is not None:
                    exc_type_name = record.exc_info[0].__name__
                else:
                    exc_type_name = "NoneType"
                
                log_data["exception"] = {
                    "type": exc_type_name,
                    "message": str(record.exc_info[1]) if record.exc_info[1] else "",
                    "traceback": self.formatException(record.exc_info)
                }
            except Exception as e:
                # Fallback para uma representação simplificada em caso de erro
                log_data["exception"] = {
                    "type": "UnknownExceptionType",
                    "message": f"Erro ao processar exceção: {str(e)}",
                    "traceback": self.formatException(record.exc_info) if hasattr(self, "formatException") else ""
                }
        
        # Adicionar atributos extras
        for key, value in record.__dict__.items():
            if key.startswith("_") and key != "_":
                try:
                    # Tentar converter para JSON
                    json.dumps(value)
                    log_data[key[1:]] = value
                except (TypeError, OverflowError):
                    # Se não for serializável, converter para string
                    log_data[key[1:]] = str(value)
        
        # Serializar para JSON
        return json.dumps(log_data)

# Configurador de log
def setup_logging(
    level: Union[int, str] = logging.INFO,
    log_file: Optional[str] = None,
    log_json: bool = False,
    app_name: str = "viticultureapi"
) -> None:
    """
    Configura o sistema de logging.
    
    Args:
        level: Nível de log
        log_file: Caminho para arquivo de log
        log_json: Se True, usa formato JSON
        app_name: Nome da aplicação
    """
    # Converter level para int se for string
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Criar handlers
    handlers = []
    
    # Handler de console
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)
    
    # Handler de arquivo
    if log_file:
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
    
    # Configurar formatters
    if log_json:
        formatter = JsonFormatter(app_name=app_name)
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Aplicar formatter aos handlers
    for handler in handlers:
        handler.setFormatter(formatter)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Adicionar handlers
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("fastapi").setLevel(level)
    
    # Mensagem de inicialização
    if not log_json:
        logging.info(f"Logging initialized: level={logging.getLevelName(level)}, file={log_file}")

# Contexto de logging para adicionar informações a todas as mensagens
class LogContext:
    """
    Contexto de logging para adicionar informações a todas as mensagens.
    
    Permite adicionar atributos extras a todas as mensagens de log
    dentro de um determinado contexto, como um ID de requisição.
    """
    
    # Alterar a anotação de tipo para permitir qualquer tipo de valor serializado como string
    _context_data: Dict[str, str] = {}
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Define um valor no contexto. Converte valores complexos para string.
        
        Args:
            key: Chave
            value: Valor
        """
        # Sempre converter qualquer valor para string para garantir compatibilidade com o tipo
        if value is None:
            cls._context_data[key] = ""
        elif isinstance(value, (dict, list, set, tuple, bool, int, float)):
            try:
                cls._context_data[key] = json.dumps(value)
            except (TypeError, ValueError):
                cls._context_data[key] = str(value)
        else:
            cls._context_data[key] = str(value)
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Obtém um valor do contexto.
        
        Args:
            key: Chave
            default: Valor padrão
            
        Returns:
            Valor associado à chave
        """
        return cls._context_data.get(key, default)
    
    @classmethod
    def remove(cls, key: str) -> None:
        """
        Remove um valor do contexto.
        
        Args:
            key: Chave
        """
        if key in cls._context_data:
            del cls._context_data[key]
    
    @classmethod
    def clear(cls) -> None:
        """Limpa todo o contexto."""
        cls._context_data.clear()
    
    @classmethod
    def get_all(cls) -> Dict[str, str]:
        """
        Obtém todos os valores do contexto.
        
        Returns:
            Dicionário com todos os valores
        """
        return cls._context_data.copy()

# Filter para adicionar contexto
class ContextFilter(logging.Filter):
    """
    Filter para adicionar contexto às mensagens de log.
    
    Adiciona os atributos do contexto a todas as mensagens de log.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtra e modifica o registro de log.
        
        Args:
            record: Registro de log
            
        Returns:
            True se o registro deve ser processado, False caso contrário
        """
        # Adicionar contexto ao registro como atributos
        for key, value in LogContext.get_all().items():
            # Atributos começando com _ para evitar conflitos com atributos padrão
            setattr(record, f"_{key}", value)
        
        return True

# Logger personalizado
class AppLogger:
    """
    Logger personalizado com recursos adicionais.
    
    Encapsula um logger padrão e adiciona recursos como:
    - Logging contextual
    - Timing de operações
    - Agrupamento de logs
    """
    
    def __init__(self, name: str):
        """
        Inicializa o logger.
        
        Args:
            name: Nome do logger
        """
        self._logger = logging.getLogger(name)
        
        # Adicionar filter de contexto
        self._context_filter = ContextFilter()
        self._logger.addFilter(self._context_filter)
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log de nível DEBUG."""
        self._log(logging.DEBUG, msg, **kwargs)
    
    def info(self, msg: str, **kwargs: Any) -> None:
        """Log de nível INFO."""
        self._log(logging.INFO, msg, **kwargs)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log de nível WARNING."""
        self._log(logging.WARNING, msg, **kwargs)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        """Log de nível ERROR."""
        self._log(logging.ERROR, msg, **kwargs)
    
    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log de nível CRITICAL."""
        self._log(logging.CRITICAL, msg, **kwargs)
    
    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        """
        Registra uma mensagem de log.
        
        Args:
            level: Nível de log
            msg: Mensagem
            **kwargs: Atributos extras
        """
        # Adicionar atributos extras
        extra = {}
        for key, value in kwargs.items():
            extra[f"_{key}"] = value
        
        # Registrar mensagem
        self._logger.log(level, msg, extra=extra)
    
    def timing(self, operation_name: str) -> "TimingContext":
        """
        Cria um contexto para medir o tempo de uma operação.
        
        Args:
            operation_name: Nome da operação
            
        Returns:
            Contexto de timing
        """
        return TimingContext(self, operation_name)
    
    def group(self, group_name: str) -> "LogGroup":
        """
        Cria um grupo de logs.
        
        Args:
            group_name: Nome do grupo
            
        Returns:
            Grupo de logs
        """
        return LogGroup(self, group_name)
    
    def with_context(self, **kwargs: Any) -> "ContextualLogger":
        """
        Cria um logger contextual.
        
        Args:
            **kwargs: Atributos de contexto
            
        Returns:
            Logger contextual
        """
        return ContextualLogger(self, **kwargs)

# Contexto de timing
class TimingContext:
    """
    Contexto para medir o tempo de uma operação.
    
    Exemplo de uso:
    ```
    with logger.timing("operation_name"):
        # Código a ser medido
    ```
    """
    
    def __init__(self, logger: AppLogger, operation_name: str):
        """
        Inicializa o contexto.
        
        Args:
            logger: Logger
            operation_name: Nome da operação
        """
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = 0
    
    def __enter__(self) -> "TimingContext":
        """Inicia o timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Registra o tempo decorrido.
        
        Args:
            exc_type: Tipo da exceção
            exc_val: Valor da exceção
            exc_tb: Traceback da exceção
        """
        elapsed_time = time.time() - self.start_time
        elapsed_ms = round(elapsed_time * 1000)
        
        # Registrar mensagem diferente dependendo do resultado
        if exc_type:
            self.logger.error(
                f"Operation '{self.operation_name}' failed after {elapsed_ms}ms",
                operation=self.operation_name,
                elapsed_ms=elapsed_ms,
                error=str(exc_val)
            )
        else:
            self.logger.info(
                f"Operation '{self.operation_name}' completed in {elapsed_ms}ms",
                operation=self.operation_name,
                elapsed_ms=elapsed_ms
            )

# Grupo de logs
class LogGroup:
    """
    Grupo de logs.
    
    Permite agrupar logs relacionados.
    
    Exemplo de uso:
    ```
    with logger.group("group_name"):
        logger.info("Mensagem 1")
        logger.info("Mensagem 2")
    ```
    """
    
    def __init__(self, logger: AppLogger, group_name: str):
        """
        Inicializa o grupo.
        
        Args:
            logger: Logger
            group_name: Nome do grupo
        """
        self.logger = logger
        self.group_name = group_name
    
    def __enter__(self) -> "LogGroup":
        """Inicia o grupo."""
        self.logger.info(f"=== BEGIN {self.group_name} ===", group=self.group_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Finaliza o grupo.
        
        Args:
            exc_type: Tipo da exceção
            exc_val: Valor da exceção
            exc_tb: Traceback da exceção
        """
        if exc_type:
            self.logger.error(
                f"=== END {self.group_name} WITH ERROR ===",
                group=self.group_name,
                error=str(exc_val)
            )
        else:
            self.logger.info(f"=== END {self.group_name} ===", group=self.group_name)

# Logger contextual
class ContextualLogger:
    """
    Logger contextual.
    
    Adiciona atributos de contexto a todas as mensagens de log.
    
    Exemplo de uso:
    ```
    ctx_logger = logger.with_context(request_id="123")
    ctx_logger.info("Mensagem")  # Terá request_id="123"
    ```
    """
    
    def __init__(self, logger: AppLogger, **context: Any):
        """
        Inicializa o logger contextual.
        
        Args:
            logger: Logger
            **context: Atributos de contexto
        """
        self.logger = logger
        self.context = context
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log de nível DEBUG."""
        self._log(logging.DEBUG, msg, **kwargs)
    
    def info(self, msg: str, **kwargs: Any) -> None:
        """Log de nível INFO."""
        self._log(logging.INFO, msg, **kwargs)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log de nível WARNING."""
        self._log(logging.WARNING, msg, **kwargs)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        """Log de nível ERROR."""
        self._log(logging.ERROR, msg, **kwargs)
    
    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log de nível CRITICAL."""
        self._log(logging.CRITICAL, msg, **kwargs)
    
    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        """
        Registra uma mensagem de log.
        
        Args:
            level: Nível de log
            msg: Mensagem
            **kwargs: Atributos extras
        """
        # Mesclar contexto com atributos extras
        all_kwargs = {**self.context, **kwargs}
        
        # Registrar mensagem
        getattr(self.logger, logging.getLevelName(level).lower())(msg, **all_kwargs)
    
    def with_context(self, **kwargs: Any) -> "ContextualLogger":
        """
        Cria um novo logger contextual com contexto adicional.
        
        Args:
            **kwargs: Atributos de contexto adicionais
            
        Returns:
            Novo logger contextual
        """
        # Mesclar contexto existente com novo contexto
        new_context = {**self.context, **kwargs}
        return ContextualLogger(self.logger, **new_context)

# Função para obter um logger
def get_logger(name: str) -> AppLogger:
    """
    Obtém um logger personalizado.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger personalizado
    """
    return AppLogger(name)
