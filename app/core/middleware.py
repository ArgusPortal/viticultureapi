"""
Middlewares da aplicação.

Define middlewares para funcionalidades como cache, tratamento de
exceções, logging de requisições, etc.
"""
import time
from typing import Callable, Dict, Any, Optional, List, Union
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send
import json
import traceback
import sys
import hashlib
from datetime import datetime, timedelta
from wsgiref.handlers import format_date_time
from time import mktime

from app.core.exceptions import BaseAppException, handle_exception
from app.models.base import ErrorResponse
from app.core.logging import get_logger, LogContext

logger = get_logger(__name__)

class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware para adicionar headers de cache-control às respostas.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        default_max_age: int = 3600, 
        cache_paths: Optional[Dict[str, int]] = None,
        no_cache_paths: Optional[List[str]] = None
    ):
        """
        Inicializa o middleware.
        
        Args:
            app: Aplicação ASGI
            default_max_age: Tempo padrão de cache em segundos
            cache_paths: Dicionário mapeando caminhos para tempos de cache
            no_cache_paths: Lista de caminhos que não devem ser cacheados
        """
        super().__init__(app)
        self.default_max_age = default_max_age
        self.cache_paths = cache_paths or {}
        self.no_cache_paths = no_cache_paths or ["/api/v1/auth/", "/docs", "/redoc"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa a requisição.
        
        Args:
            request: Requisição
            call_next: Callback para próximo middleware
            
        Returns:
            Resposta
        """
        # Processar requisição
        response = await call_next(request)
        
        # Verificar se o caminho deve ter cache
        path = request.url.path
        
        # Verificar se o caminho está na lista de no_cache
        for no_cache_path in self.no_cache_paths:
            if path.startswith(no_cache_path):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                return response
        
        # Verificar se é uma requisição GET (apenas GETs são cacheados)
        if request.method != "GET":
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response
        
        # Define a default max_age value first to avoid UnboundLocalError
        max_age = self.default_max_age
        
        # Check if Cache-Control header already exists and should be preserved
        if "Cache-Control" not in response.headers:
            # Determinar max-age com base no caminho
            for cache_path, age in self.cache_paths.items():
                if path.startswith(cache_path):
                    max_age = age
                    break
            
            # Set the Cache-Control header using the determined max_age
            response.headers["Cache-Control"] = f"public, max-age={max_age}"
        
        # Add Expires header if it doesn't exist
        if "Expires" not in response.headers:
            expiry_time = (datetime.utcnow() + timedelta(seconds=max_age)).strftime("%a, %d %b %Y %H:%M:%S GMT")
            response.headers["Expires"] = expiry_time
        
        # Try to add ETag header if it doesn't exist and response has a body
        if "ETag" not in response.headers and hasattr(response, "body"):
            try:
                # Garantir que o body existe e não é vazio antes de calcular o ETag
                if response.body:
                    etag = hashlib.md5(response.body).hexdigest()
                    response.headers["ETag"] = f'"{etag}"'
            except Exception as e:
                logger.warning(f"Erro ao gerar ETag: {str(e)}")
        
        return response

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware para tratamento centralizado de exceções.
    
    Captura todas as exceções lançadas durante o processamento de requisições
    e retorna respostas JSON padronizadas.
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        include_traceback: bool = False
    ):
        """
        Inicializa o middleware.
        
        Args:
            app: Aplicação ASGI
            include_traceback: Se True, inclui traceback na resposta (apenas em ambiente de desenvolvimento)
        """
        super().__init__(app)
        self.include_traceback = include_traceback
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa a requisição.
        
        Args:
            request: Requisição
            call_next: Callback para próximo middleware
            
        Returns:
            Resposta
        """
        try:
            return await call_next(request)
        except Exception as exc:
            # Converter para exceção da aplicação
            app_exception = handle_exception(exc) if not isinstance(exc, BaseAppException) else exc
            
            # Criar resposta padronizada
            error_response = {
                "detail": app_exception.message,
                "status_code": app_exception.status_code
            }
            
            # Adicionar código de erro se disponível
            if app_exception.error_code:
                error_response["code"] = app_exception.error_code
            
            # Adicionar detalhes se disponíveis
            if app_exception.details:
                error_response["details"] = app_exception.details
            
            # Adicionar traceback em desenvolvimento
            if self.include_traceback:
                error_response["traceback"] = app_exception.traceback_info
            
            # Registrar erro
            logger.error(
                f"Error handling request to {request.url.path}: {app_exception.message}",
                exc_info=True
            )
            
            # Retornar resposta JSON
            return JSONResponse(
                status_code=app_exception.status_code,
                content=error_response
            )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de requisições.
    
    Registra informações sobre as requisições recebidas e suas respostas,
    como método, caminho, código de status, tempo de resposta, etc.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa a requisição.
        
        Args:
            request: Requisição
            call_next: Callback para próximo middleware
            
        Returns:
            Resposta
        """
        # Registrar início da requisição
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "-")
        
        # Adicionar request_id ao contexto de logging
        LogContext.set("request_id", request_id)
        
        # Registrar detalhes da requisição
        client_host = request.client.host if request.client else "unknown"
        request_info = {
            "id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": client_host,
            "user_agent": request.headers.get("User-Agent", "-")
        }
        
        logger.info(f"Request received: {json.dumps(request_info)}")
        
        # Processar requisição
        try:
            response = await call_next(request)
            
            # Calcular tempo de resposta
            process_time = time.time() - start_time
            response_time_ms = round(process_time * 1000)
            
            # Adicionar header com tempo de resposta
            response.headers["X-Process-Time"] = f"{response_time_ms} ms"
            
            # Adicionar request_id à resposta para correlação
            response.headers["X-Request-ID"] = request_id
            
            # Registrar detalhes da resposta
            response_info = {
                "id": request_id,
                "status_code": response.status_code,
                "process_time_ms": response_time_ms,
                "content_type": response.headers.get("Content-Type", "-"),
                "content_length": response.headers.get("Content-Length", "-")
            }
            
            log_method = logger.info if response.status_code < 400 else logger.warning
            log_method(f"Response sent: {json.dumps(response_info)}")
            
            return response
        except Exception as e:
            # Calcular tempo até erro
            process_time = time.time() - start_time
            response_time_ms = round(process_time * 1000)
            
            # Registrar erro
            error_info = {
                "id": request_id,
                "error": str(e),
                "process_time_ms": response_time_ms
            }
            
            logger.error(f"Error processing request: {json.dumps(error_info)}")
            
            # Re-lançar exceção para ser tratada pelo próximo middleware
            raise
        finally:
            # Limpar o contexto de logging
            LogContext.remove("request_id")

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware para garantir que todas as requisições tenham um ID único.
    
    Se a requisição não tiver um cabeçalho X-Request-ID, um é gerado.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa a requisição.
        
        Args:
            request: Requisição
            call_next: Callback para próximo middleware
            
        Returns:
            Resposta
        """
        # Verificar se já tem um request_id
        request_id = request.headers.get("X-Request-ID")
        
        # Se não tiver, gerar um
        if not request_id:
            import uuid
            request_id = str(uuid.uuid4())
            # Não é possível modificar os headers da requisição diretamente,
            # mas podemos adicionar ao contexto para uso posterior
            request.state.request_id = request_id
        
        # Processar requisição
        response = await call_next(request)
        
        # Adicionar request_id à resposta
        response.headers["X-Request-ID"] = request_id
        
        return response

def setup_middlewares(app: FastAPI) -> None:
    """
    Configura todos os middlewares da aplicação.
    
    Args:
        app: Aplicação FastAPI
    """
    # Adicionar middleware de request ID (primeiro, para estar disponível para os outros)
    app.add_middleware(RequestIDMiddleware)
    
    # Adicionar middleware de logging de requisições
    app.add_middleware(RequestLoggingMiddleware)
    
    # Adicionar middleware de tratamento de exceções
    app.add_middleware(
        ErrorHandlerMiddleware,
        include_traceback=app.debug
    )
    
    # Adicionar middleware de cache
    app.add_middleware(
        CacheControlMiddleware,
        default_max_age=3600,  # 1 hora
        cache_paths={
            "/api/v1/production/": 86400,  # 24 horas
            "/api/v1/imports/": 86400,
            "/api/v1/exports/": 86400,
            "/api/v1/processing/": 86400,
            "/api/v1/commercialization/": 86400,
        },
        no_cache_paths=[
            "/api/v1/auth/",
            "/api/v1/cache/",
            "/api/v1/diagnostics/",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    )
