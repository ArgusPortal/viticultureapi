"""
Endpoints de diagnóstico para a aplicação.

Fornece informações sobre logs, rotas, dependências e permite testar o sistema de tratamento de exceções.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import os
import platform

from app.core.security import verify_token
from app.core.exceptions import InternalServerException, BadRequestException, NotFoundException, ForbiddenException, UnauthorizedException, ValidationException, ServiceUnavailableException

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/logs", summary="Logs recentes")
async def get_recent_logs(
    lines: int = Query(100, ge=1, le=1000, description="Número de linhas para retornar"),
    level: str = Query("INFO", description="Nível mínimo de log"),
    current_user: str = Depends(verify_token)
):
    """
    Obtém os logs mais recentes da aplicação.
    
    Permite filtrar por nível e limitar o número de linhas.
    """
    try:
        # Converter nível de log para int
        level_int = getattr(logging, level.upper(), logging.INFO)
        
        # Caminho do arquivo de log
        log_file = os.getenv("LOG_FILE", "app.log")
        
        if not os.path.exists(log_file):
            return {
                "status": "warning",
                "message": f"Arquivo de log '{log_file}' não encontrado",
                "logs": []
            }
        
        # Ler as últimas linhas do arquivo de log
        with open(log_file, 'r', encoding='utf-8') as f:
            # Carregar todas as linhas em memória (não é ideal para arquivos muito grandes)
            all_lines = f.readlines()
            
            # Filtrar linhas pelo nível de log
            filtered_lines = []
            for line in all_lines:
                # Extrair nível do log (assumindo formato padrão)
                try:
                    # Tentar extrair nível de formatos comuns
                    if " - INFO - " in line:
                        log_level = logging.INFO
                    elif " - WARNING - " in line:
                        log_level = logging.WARNING
                    elif " - ERROR - " in line:
                        log_level = logging.ERROR
                    elif " - CRITICAL - " in line:
                        log_level = logging.CRITICAL
                    elif " - DEBUG - " in line:
                        log_level = logging.DEBUG
                    else:
                        # Se não conseguir extrair, assume INFO
                        log_level = logging.INFO
                    
                    # Filtrar pelo nível
                    if log_level >= level_int:
                        filtered_lines.append(line.strip())
                except:
                    # Se houver erro na análise, inclui a linha
                    filtered_lines.append(line.strip())
            
            # Obter as últimas N linhas
            recent_logs = filtered_lines[-lines:] if filtered_lines else []
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "log_file": log_file,
            "level_filter": level,
            "total_lines": len(filtered_lines),
            "returned_lines": len(recent_logs),
            "logs": recent_logs
        }
    except Exception as e:
        logger.error(f"Erro ao obter logs: {str(e)}", exc_info=True)
        raise InternalServerException(
            message="Erro ao obter logs",
            details={"error": str(e)},
            original_exception=e
        )

@router.get("/errors", summary="Erros recentes")
async def get_recent_errors(
    lines: int = Query(50, ge=1, le=500, description="Número de erros para retornar"),
    current_user: str = Depends(verify_token)
):
    """
    Obtém os erros mais recentes registrados nos logs.
    
    Filtra apenas entradas de nível ERROR ou superior.
    """
    return await get_recent_logs(lines=lines, level="ERROR", current_user=current_user)

@router.get("/routes", summary="Rotas da aplicação")
async def get_routes(current_user: str = Depends(verify_token)):
    """
    Lista todas as rotas registradas na aplicação.
    
    Útil para verificar quais endpoints estão disponíveis.
    """
    from fastapi import FastAPI
    from app.main import app
    
    try:
        # Obter todas as rotas registradas
        routes = []
        
        for route in app.routes:
            # Usar um dicionário com valores padrão para evitar erros
            route_info = {
                "path": str(getattr(route, "path", "unknown")),
                "name": str(getattr(route, "name", "unnamed")),
                "methods": [],
                "endpoint": None,
                "summary": None,
                "tags": [],
                "response_model": None
            }
            
            # Verificar métodos HTTP com segurança
            try:
                methods = getattr(route, "methods", None)
                if methods and hasattr(methods, "__iter__"):
                    # Converter de set para list se necessário
                    route_info["methods"] = [str(m) for m in methods]
            except Exception as e:
                logger.debug(f"Erro ao acessar methods: {str(e)}")
            
            # Verificar endpoint com segurança
            try:
                endpoint = getattr(route, "endpoint", None)
                if endpoint:
                    if hasattr(endpoint, "__name__"):
                        route_info["endpoint"] = str(endpoint.__name__)
                    else:
                        route_info["endpoint"] = str(endpoint)
            except Exception as e:
                logger.debug(f"Erro ao acessar endpoint: {str(e)}")
            
            # Verificar sumário com segurança
            try:
                summary = getattr(route, "summary", None)
                if summary:
                    route_info["summary"] = str(summary)
            except Exception as e:
                logger.debug(f"Erro ao acessar summary: {str(e)}")
            
            # Verificar tags com segurança
            try:
                tags = getattr(route, "tags", None)
                if tags and hasattr(tags, "__iter__"):
                    route_info["tags"] = [str(t) for t in tags]
            except Exception as e:
                logger.debug(f"Erro ao acessar tags: {str(e)}")
            
            # Verificar modelo de resposta com segurança
            try:
                response_model = getattr(route, "response_model", None)
                if response_model:
                    route_info["response_model"] = str(response_model)
            except Exception as e:
                logger.debug(f"Erro ao acessar response_model: {str(e)}")
            
            routes.append(route_info)
        
        # Agrupar por tag de forma segura
        routes_by_tag = {}
        for route in routes:
            # Assegurar que tags é uma lista e não None
            tags = route.get("tags", []) or ["no_tag"]
            
            # Se tags não for iterável por alguma razão, usar fallback
            if not hasattr(tags, "__iter__"):
                tags = ["no_tag"]
                
            # Converter elementos não-string para string
            for tag in tags:
                tag_str = str(tag)
                if tag_str not in routes_by_tag:
                    routes_by_tag[tag_str] = []
                routes_by_tag[tag_str].append(route)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_routes": len(routes),
            "routes_by_tag": routes_by_tag,
            "all_routes": routes
        }
    except Exception as e:
        logger.error(f"Erro ao obter rotas: {str(e)}", exc_info=True)
        raise InternalServerException(
            message="Erro ao obter rotas",
            details={"error": str(e)},
            original_exception=e
        )

@router.get("/dependencies", summary="Dependências da aplicação")
async def get_dependencies(current_user: str = Depends(verify_token)):
    """
    Lista todas as dependências Python instaladas.
    
    Útil para verificar versões de pacotes e requisitos.
    """
    try:
        import sys
        import platform
        
        # Obter todas as dependências instaladas usando uma abordagem diferente
        installed_packages = []
        error_message = None
        
        # Método 1: Usar subprocess para executar pip freeze
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"], 
                capture_output=True, 
                text=True, 
                check=False  # Não lançar exceção se o comando falhar
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "==" in line:
                        try:
                            name, version = line.strip().split("==", 1)
                            installed_packages.append({
                                "name": name,
                                "version": version,
                                "location": None
                            })
                        except ValueError:
                            # Linhas que não seguem o formato padrão (como editable installs)
                            continue
            else:
                error_message = f"pip freeze falhou: {result.stderr}"
                logger.warning(error_message)
        except Exception as e:
            error_message = f"Erro ao executar pip freeze: {str(e)}"
            logger.warning(error_message)
        
        # Método 2: Se pip freeze falhou e o Python é 3.8+, usar importlib.metadata
        if not installed_packages:
            try:
                # importlib.metadata foi introduzido no Python 3.8
                try:
                    import importlib.metadata as metadata
                except ImportError:
                    # Fallback para Python < 3.8
                    import importlib_metadata as metadata
                
                for dist in metadata.distributions():
                    try:
                        installed_packages.append({
                            "name": dist.metadata["Name"],
                            "version": dist.version,
                            "location": str(dist.locate_file(""))
                        })
                    except Exception as e:
                        logger.debug(f"Erro ao processar distribuição {dist}: {str(e)}")
            except Exception as e:
                if error_message:
                    error_message += f"; Erro com importlib.metadata: {str(e)}"
                else:
                    error_message = f"Erro com importlib.metadata: {str(e)}"
                logger.warning(error_message)
        
        # Método 3: Último recurso - usar o módulo pkg_resources sem iteração
        if not installed_packages:
            try:
                import pkg_resources
                
                # Lista de pacotes comuns para checar individualmente
                common_packages = [
                    "fastapi", "uvicorn", "pydantic", "starlette", "requests", 
                    "beautifulsoup4", "python-dotenv", "pandas", "numpy", 
                    "matplotlib", "seaborn", "plotly", "scipy", "statsmodels",
                    "dash", "streamlit", "pytest", "httpx", "jose", "passlib"
                ]
                
                for package_name in common_packages:
                    try:
                        # Tenta obter a distribuição sem usar working_set
                        dist = pkg_resources.get_distribution(package_name)
                        installed_packages.append({
                            "name": dist.key,
                            "version": dist.version,
                            "location": dist.location if hasattr(dist, "location") else None
                        })
                    except pkg_resources.DistributionNotFound:
                        # Pacote não está instalado, ignorar
                        pass
                    except Exception as e:
                        logger.debug(f"Erro ao verificar pacote {package_name}: {str(e)}")
            except Exception as e:
                if error_message:
                    error_message += f"; Erro com pkg_resources: {str(e)}"
                else:
                    error_message = f"Erro com pkg_resources: {str(e)}"
                logger.warning(error_message)
        
        # Informações do ambiente Python
        python_info = {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
            "path": sys.path,
            "executable": sys.executable,
            "platform": sys.platform
        }
        
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "python": python_info,
            "total_packages": len(installed_packages),
            "packages": sorted(installed_packages, key=lambda x: x["name"].lower())
        }
        
        # Adicionar mensagem de erro se houve problemas
        if error_message:
            response["warning"] = error_message
        
        return response
    except Exception as e:
        logger.error(f"Erro ao obter dependências: {str(e)}", exc_info=True)
        raise InternalServerException(
            message="Erro ao obter dependências",
            details={"error": str(e)},
            original_exception=e
        )

@router.post("/test-error", summary="Testar tratamento de exceções")
async def test_error_handling(
    error_type: str = Query("internal", description="Tipo de erro para testar"),
    current_user: str = Depends(verify_token)
):
    """
    Endpoint para testar o sistema de tratamento de exceções.
    
    Permite simular diferentes tipos de erros para verificar o comportamento do sistema.
    
    Opções para error_type:
    - internal: Erro interno do servidor (500)
    - not_found: Recurso não encontrado (404)
    - forbidden: Acesso proibido (403)
    - unauthorized: Não autorizado (401)
    - validation: Erro de validação (400)
    - timeout: Timeout de serviço (503)
    - python: Exceção Python pura
    """
    # Mapeamento de tipos de erro para exceções
    error_mapping = {
        "internal": InternalServerException(message="Erro interno de teste"),
        "not_found": NotFoundException(message="Recurso não encontrado de teste"),
        "forbidden": ForbiddenException(message="Acesso proibido de teste"),
        "unauthorized": UnauthorizedException(message="Não autorizado de teste"),
        "validation": ValidationException(
            message="Erro de validação de teste",
            field_errors={"field1": ["Valor inválido"], "field2": ["Campo obrigatório"]}
        ),
        "timeout": ServiceUnavailableException(message="Timeout de serviço de teste"),
    }
    
    # Obter exceção do mapeamento ou lançar exceção Python pura
    if error_type in error_mapping:
        raise error_mapping[error_type]
    elif error_type == "python":
        # Lançar exceção Python pura
        raise ValueError("Exceção Python pura de teste")
    else:
        # Erro sobre tipo inválido
        raise BadRequestException(
            message="Tipo de erro inválido",
            details={"error_type": error_type, "valid_types": list(error_mapping.keys()) + ["python"]}
        )