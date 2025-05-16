"""
Sistema de relatórios de qualidade de dados.

Fornece mecanismos para relatar problemas de qualidade em dados.
"""
import json
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import os
import csv

from app.core.validation.interface import ValidationIssue, ValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)

class ValidationReporter:
    """Gerador de relatórios de validação."""
    
    def __init__(self, report_name: Optional[str] = None):
        """
        Inicializa o gerador de relatórios.
        
        Args:
            report_name: Nome do relatório (opcional)
        """
        self.report_name = report_name or f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def generate_summary(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """
        Gera um resumo dos problemas de validação.
        
        Args:
            validation_result: Resultado da validação
            
        Returns:
            Resumo dos problemas
        """
        # Contar ocorrências de cada tipo de problema
        issues_by_severity = {}
        for severity in ValidationSeverity:
            count = len(validation_result.get_issues_by_severity(severity))
            if count > 0:
                issues_by_severity[severity.value] = count
        
        # Contar ocorrências por campo
        fields_with_issues = {}
        all_fields = set(issue.field for issue in validation_result.issues)
        
        for field in all_fields:
            field_issues = validation_result.get_issues_by_field(field)
            fields_with_issues[field] = {
                "total": len(field_issues),
                "by_severity": {
                    severity.value: len([i for i in field_issues if i.severity == severity])
                    for severity in ValidationSeverity
                    if len([i for i in field_issues if i.severity == severity]) > 0
                }
            }
        
        # Gerar resumo
        return {
            "report_name": self.report_name,
            "timestamp": datetime.now().isoformat(),
            "is_valid": validation_result.is_valid,
            "total_issues": len(validation_result.issues),
            "issues_by_severity": issues_by_severity,
            "fields_with_issues": fields_with_issues
        }
    
    def to_json(self, validation_result: ValidationResult, file_path: Optional[str] = None) -> str:
        """
        Converte o resultado da validação para JSON.
        
        Args:
            validation_result: Resultado da validação
            file_path: Caminho para salvar o arquivo (opcional)
            
        Returns:
            String JSON com o relatório
        """
        # Criar estrutura do relatório
        report = {
            "report_name": self.report_name,
            "timestamp": datetime.now().isoformat(),
            "is_valid": validation_result.is_valid,
            "total_issues": len(validation_result.issues),
            "issues": [issue.to_dict() for issue in validation_result.issues],
            "summary": self.generate_summary(validation_result)
        }
        
        # Converter para JSON
        json_report = json.dumps(report, indent=2, ensure_ascii=False)
        
        # Salvar em arquivo se especificado
        if file_path:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_report)
        
        return json_report
    
    def to_csv(self, validation_result: ValidationResult, file_path: str) -> None:
        """
        Salva os problemas de validação em um arquivo CSV.
        
        Args:
            validation_result: Resultado da validação
            file_path: Caminho para salvar o arquivo
        """
        # Preparar dados para CSV
        rows = []
        for issue in validation_result.issues:
            row = {
                "field": issue.field,
                "severity": issue.severity.value,
                "message": issue.message,
                "code": issue.code,
                "value": str(issue.value) if issue.value is not None else ""
            }
            rows.append(row)
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Escrever CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            else:
                f.write("No validation issues found")
    
    def to_dataframe(self, validation_result: ValidationResult) -> pd.DataFrame:
        """
        Converte o resultado da validação para um DataFrame.
        
        Args:
            validation_result: Resultado da validação
            
        Returns:
            DataFrame com os problemas de validação
        """
        # Preparar dados para o DataFrame
        data = []
        for issue in validation_result.issues:
            row = {
                "field": issue.field,
                "severity": issue.severity.value,
                "message": issue.message,
                "code": issue.code,
                "value": str(issue.value) if issue.value is not None else None
            }
            # Adicionar detalhes como colunas adicionais
            if issue.details:
                for k, v in issue.details.items():
                    row[f"detail_{k}"] = str(v)
            
            data.append(row)
        
        # Criar DataFrame
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame(columns=["field", "severity", "message", "code", "value"])
    
    def log_issues(self, validation_result: ValidationResult, min_severity: ValidationSeverity = ValidationSeverity.WARNING) -> None:
        """
        Registra os problemas de validação no log.
        
        Args:
            validation_result: Resultado da validação
            min_severity: Severidade mínima para registro
        """
        # Mapear severidades para níveis de log
        severity_to_log = {
            ValidationSeverity.INFO: logger.info,
            ValidationSeverity.WARNING: logger.warning,
            ValidationSeverity.ERROR: logger.error,
            ValidationSeverity.CRITICAL: logger.critical
        }
        
        # Registrar resumo
        logger.info(f"Validation report: {self.report_name}")
        logger.info(f"Total issues: {len(validation_result.issues)}, Is valid: {validation_result.is_valid}")
        
        # Registrar problemas individuais
        severities = [s for s in ValidationSeverity if s.value >= min_severity.value]
        for severity in severities:
            issues = validation_result.get_issues_by_severity(severity)
            if issues:
                log_func = severity_to_log.get(severity, logger.info)
                for issue in issues:
                    log_func(f"{issue.field}: {issue.message} [Code: {issue.code}]")

class DataQualityMonitor:
    """
    Monitor de qualidade de dados.
    
    Permite acompanhar a qualidade dos dados ao longo do tempo,
    armazenando métricas e problemas encontrados.
    """
    
    def __init__(
        self,
        name: str,
        storage_dir: Optional[str] = None
    ):
        """
        Inicializa o monitor de qualidade.
        
        Args:
            name: Nome do monitor
            storage_dir: Diretório para armazenamento de relatórios
        """
        self.name = name
        self.storage_dir = storage_dir or os.path.join("data_quality", "reports", name)
        self.reporter = ValidationReporter(name)
        
        # Criar diretório se não existir
        if self.storage_dir:
            os.makedirs(self.storage_dir, exist_ok=True)
    
    def record_validation(
        self,
        validation_result: ValidationResult,
        context: Optional[Dict[str, Any]] = None,
        save_report: bool = True
    ) -> Dict[str, Any]:
        """
        Registra uma validação no monitor.
        
        Args:
            validation_result: Resultado da validação
            context: Informações contextuais (opcional)
            save_report: Se deve salvar os relatórios em disco
            
        Returns:
            Resumo da validação
        """
        timestamp = datetime.now()
        report_id = f"{self.name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Gerar resumo
        summary = self.reporter.generate_summary(validation_result)
        if context:
            summary["context"] = context
        
        # Salvar relatórios se solicitado
        if save_report and self.storage_dir:
            # JSON completo
            json_path = os.path.join(self.storage_dir, f"{report_id}.json")
            self.reporter.to_json(validation_result, json_path)
            
            # CSV dos problemas
            csv_path = os.path.join(self.storage_dir, f"{report_id}.csv")
            self.reporter.to_csv(validation_result, csv_path)
            
            # Registrar caminhos no resumo
            summary["report_paths"] = {
                "json": json_path,
                "csv": csv_path
            }
        
        # Registrar problemas críticos no log
        self.reporter.log_issues(
            validation_result,
            min_severity=ValidationSeverity.ERROR
        )
        
        return summary
    
    def get_historical_metrics(self, days: int = 30) -> pd.DataFrame:
        """
        Obtém métricas históricas de qualidade.
        
        Args:
            days: Número de dias a retroceder
            
        Returns:
            DataFrame com métricas históricas
        """
        if not self.storage_dir or not os.path.exists(self.storage_dir):
            return pd.DataFrame()
        
        # Filtrar por data
        cutoff_date = datetime.now() - pd.Timedelta(days=days)
        
        # Coletar relatórios
        reports = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(self.storage_dir, filename)
                    file_date = datetime.strptime(
                        filename.split("_")[1].split(".")[0],
                        "%Y%m%d%H%M%S"
                    )
                    
                    if file_date >= cutoff_date:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                            reports.append({
                                "date": file_date,
                                "is_valid": report_data.get("is_valid", False),
                                "total_issues": report_data.get("total_issues", 0),
                                "critical_issues": sum(1 for i in report_data.get("issues", []) 
                                                     if i.get("severity") == ValidationSeverity.CRITICAL.value),
                                "error_issues": sum(1 for i in report_data.get("issues", []) 
                                                  if i.get("severity") == ValidationSeverity.ERROR.value),
                                "warning_issues": sum(1 for i in report_data.get("issues", []) 
                                                    if i.get("severity") == ValidationSeverity.WARNING.value)
                            })
                except Exception as e:
                    logger.error(f"Error processing report file {filename}: {str(e)}")
        
        if reports:
            return pd.DataFrame(reports).sort_values("date")
        else:
            return pd.DataFrame(columns=["date", "is_valid", "total_issues", 
                                        "critical_issues", "error_issues", "warning_issues"])
