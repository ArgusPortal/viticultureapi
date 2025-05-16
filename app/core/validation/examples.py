"""
Exemplos de uso do sistema de validação.

Demonstra como utilizar os componentes de validação em conjunto com o pipeline.
"""
import pandas as pd
import numpy as np  # Import não utilizado diretamente
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union  # Union não é utilizado
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import validators, including DictValidator and ListValidator
from app.core.pipeline import Pipeline
from app.core.validation.validators import (
    DictValidator, ListValidator, StringValidator, NumericValidator,
    DateValidator, DataFrameValidator
)
from app.core.validation import (
    # Interfaces
    ValidationSeverity, ValidationIssue, ValidationResult, Validator,
    
    # Normalizadores
    StringNormalizer, NumericNormalizer, DateNormalizer,
    
    # Integração com Pipeline
    ValidatingPipelineTransformer, NormalizingPipelineTransformer,
    ValidatingDataFrameTransformer, NormalizingDataFrameTransformer,
    ValidationPipelineFactory,
    
    # Relatórios
    ValidationReporter, DataQualityMonitor
)

# Import necessary pipeline components
from app.core.pipeline import (
    DataFrameTransformer, CSVExtractor, DataFrameToCSVLoader
)


def exemplo_validacao_dados_simples():
    """Exemplo simples de validação de dados."""
    # Criar um validador de strings
    validator = StringValidator(
        field_name="nome_vinho",
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-ZáàâãéèêíóôõúçÁÀÂÃÉÈÍÓÔÕÚÇ\s\-]+$',
        required=True
    )
    
    # Validar diferentes valores
    resultado1 = validator.validate("Cabernet Sauvignon")
    print(f"Válido: {resultado1.is_valid}")
    
    resultado2 = validator.validate("C@bernet")
    print(f"Válido: {resultado2.is_valid}")
    
    # Exibir problemas do segundo resultado
    for issue in resultado2.issues:
        print(f"- {issue}")


def exemplo_normalizacao_dados():
    """Exemplo de normalização de dados."""
    # Criar um normalizador de strings
    normalizer = StringNormalizer(
        field_name="regiao",
        strip=True,
        uppercase=True,
        remove_accents=True,
        validator=StringValidator(field_name="regiao", required=True)
    )
    
    # Normalizar uma string
    valor_normalizado, resultado = normalizer.normalize("  Vale dos Vinhedos  ")
    print(f"Normalizado: '{valor_normalizado}'")
    print(f"Válido: {resultado.is_valid}")
    
    # Criar um normalizador numérico
    num_normalizer = NumericNormalizer(
        field_name="temperatura",
        decimal_places=1,
        validator=NumericValidator(
            field_name="temperatura",
            min_value=15,
            max_value=25
        )
    )
    
    # Normalizar valores numéricos
    for valor in ["22,5", "  18.3  ", 30, "frio"]:
        normalizado, resultado = num_normalizer.normalize(valor)
        print(f"Original: {valor}, Normalizado: {normalizado}, Válido: {resultado.is_valid}")
        if not resultado.is_valid:
            print(f"  Problemas: {len(resultado.issues)}")
            for issue in resultado.issues:
                print(f"  - {issue}")


def exemplo_validacao_dataframe():
    """Exemplo de validação de DataFrame."""
    # Criar DataFrame de exemplo (dados de produção vinícola)
    df = pd.DataFrame({
        'ano': [2020, 2021, 2022, None, 2023],
        'regiao': ['Serra Gaúcha', 'Vale do São Francisco', 'Campanha Gaúcha', 'Serra Gaúcha', 'Vale Central'],
        'uva': ['Cabernet', 'Merlot', 'Malbec', 'Chardonnay', 'Carménère'],
        'producao_ton': [1500, 800, 1200, 900, -100],
        'area_hectares': [350, 200, 280, 220, 300]
    })
    
    # Criar validadores para as colunas
    column_validators = {
        'ano': NumericValidator('ano', min_value=2000, max_value=datetime.now().year, is_integer=True),
        'regiao': StringValidator('regiao', min_length=3, required=True),
        'uva': StringValidator('uva', min_length=2, required=True),
        'producao_ton': NumericValidator('producao_ton', min_value=0, allow_zero=False),
        'area_hectares': NumericValidator('area_hectares', min_value=1)
    }
    
    # Criar validador de DataFrame
    df_validator = DataFrameValidator(
        field_name="dados_producao",
        column_validators=column_validators,
        min_rows=1
    )
    
    # Validar o DataFrame
    resultado = df_validator.validate(df)
    
    # Exibir resumo da validação
    print(f"DataFrame válido: {resultado.is_valid}")
    print(f"Total de problemas: {len(resultado.issues)}")
    
    # Exibir problemas encontrados
    for issue in resultado.issues:
        print(f"- {issue}")
    
    # Gerar relatório
    reporter = ValidationReporter("exemplo_validacao_df")
    relatorio_json = reporter.to_json(resultado)
    print("\nRelatório JSON:")
    print(relatorio_json[:200] + "...")  # Mostrar apenas o início do JSON


# Extract transformer out of function scope for reuse
class LimpezaDadosTransformer(DataFrameTransformer):
    """Transformer for data cleaning operations."""
    
    def __init__(self, price_column='preco'):
        super().__init__("limpeza_dados")
        self.price_column = price_column
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        # Remove duplicate rows
        data = self.drop_duplicates(data)
        
        # Fill missing values in price column if it exists
        if self.price_column in data.columns:
            data[self.price_column] = data[self.price_column].fillna(data[self.price_column].mean())
        
        return data


def create_wine_validators():
    """Create validators for wine data columns."""
    return {
        'nome': StringValidator('nome', min_length=2, required=True),
        'tipo': StringValidator('tipo', allowed_values=["Tinto", "Branco", "Rosé", "Espumante"]),
        'safra': NumericValidator('safra', min_value=1900, max_value=datetime.now().year, is_integer=True),
        'preco': NumericValidator('preco', min_value=0, allow_zero=False)
    }


def create_wine_normalizers():
    """Create normalizers for wine data columns."""
    return {
        'nome': StringNormalizer('nome', strip=True, remove_accents=False),
        'tipo': StringNormalizer('tipo', strip=True, uppercase=True),
        'preco': NumericNormalizer('preco', decimal_places=2)
    }


def create_validation_pipeline(
    input_file="data/raw/vinhos.csv",
    output_file="data/processed/vinhos_validados.csv",
    report_dir="reports/validation",
    fail_on_invalid=False
):
    """Create a complete validation pipeline for wine data."""
    # Create extractor
    extractor = CSVExtractor(input_file)
    
    # Create transformers
    limpeza_transformer = LimpezaDadosTransformer()
    
    # Create validation transformer
    validacao_transformer = ValidationPipelineFactory.create_validating_dataframe_transformer(
        name="validacao_vinhos",
        column_validators=create_wine_validators(),
        required_columns=['nome', 'tipo', 'safra', 'preco'],
        fail_on_invalid=fail_on_invalid,
        report_dir=report_dir
    )
    
    # Create normalization transformer
    normalizacao_transformer = ValidationPipelineFactory.create_normalizing_dataframe_transformer(
        name="normalizacao_vinhos",
        column_normalizers=create_wine_normalizers(),
        report_dir=report_dir
    )
    
    # Create loader
    loader = DataFrameToCSVLoader(output_file)
    
    # Build complete pipeline
    pipeline = Pipeline()
    pipeline.add_extractor(extractor)
    
    for transformer in [limpeza_transformer, validacao_transformer, normalizacao_transformer]:
        pipeline.add_transformer(transformer)
    
    pipeline.add_loader(loader)
    
    return pipeline


def exemplo_pipeline_com_validacao():
    """Exemplo de pipeline com validação integrada."""
    # Usar imports diretos já estão no topo do arquivo
    
    # Criar e executar pipeline com configuração padrão
    pipeline = create_validation_pipeline()
    resultado = pipeline.execute()
    print(f"Pipeline executado com sucesso: {resultado}")
    
    # Verificar relatórios de validação gerados
    import os
    report_dir = "reports/validation"
    if os.path.exists(report_dir):
        print("\nRelatórios de validação gerados:")
        for arquivo in os.listdir(report_dir):
            print(f"- {arquivo}")


def exemplo_monitoramento_qualidade():
    """Exemplo de monitoramento de qualidade de dados."""
    # Configurar diretório para monitoramento
    os.makedirs("data_quality/reports/producao_vinicola", exist_ok=True)
    
    # Criar monitor de qualidade
    monitor = DataQualityMonitor(
        name="producao_vinicola",
        storage_dir="data_quality/reports/producao_vinicola"
    )
    
    # Função auxiliar para simular validação
    def simular_validacao(data_simulada: datetime, problemas: int, erros: int):
        # Criar resultado de validação
        result = ValidationResult()
        
        # Adicionar problemas de warning
        for i in range(problemas - erros):
            result.add_issue(ValidationIssue(
                field=f"campo_{i}",
                message=f"Aviso sobre dado suspeito no registro {i}",
                severity=ValidationSeverity.WARNING,
                value=i,
                details={"data_simulada": data_simulada.strftime("%Y-%m-%d")}
            ))
        
        # Adicionar problemas de erro
        for i in range(erros):
            result.add_issue(ValidationIssue(
                field=f"campo_erro_{i}",
                message=f"Erro de validação no registro {i}",
                severity=ValidationSeverity.ERROR,
                value=f"valor_invalido_{i}",
                details={"data_simulada": data_simulada.strftime("%Y-%m-%d")}
            ))
        
        # Registrar no monitor
        context = {
            "data_simulada": data_simulada.strftime("%Y-%m-%d"),
            "fonte": "simulacao",
            "total_registros": 1000
        }
        
        return monitor.record_validation(result, context=context)
    
    # Simular validações em diferentes datas
    hoje = datetime.now()
    resultados = []
    
    for i in range(5):
        # Using timedelta for proper date arithmetic which correctly handles month boundaries
        data = hoje - timedelta(days=i)
        # Simular melhoria gradual na qualidade dos dados (redução de erros)
        problemas = max(10 - i, 5)
        erros = max(5 - i, 0)
        
        resumo = simular_validacao(data, problemas, erros)
        resultados.append(resumo)
        print(f"Validação {i+1}: {data.strftime('%Y-%m-%d')} - " 
              f"Problemas: {problemas}, Erros: {erros}, Válido: {resumo['is_valid']}")
    
    # Obter métricas históricas
    metricas = monitor.get_historical_metrics(days=7)
    
    print("\nMétricas históricas:")
    print(metricas)
    
    # Visualizar evolução da qualidade (opcional se matplotlib estiver disponível)
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 6))
        plt.plot(metricas['date'], metricas['total_issues'], 'r-', label='Problemas Totais')
        plt.plot(metricas['date'], metricas['error_issues'], 'b--', label='Erros')
        plt.plot(metricas['date'], metricas['warning_issues'], 'y:', label='Avisos')
        
        plt.title('Evolução da Qualidade de Dados')
        plt.xlabel('Data')
        plt.ylabel('Número de Problemas')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        
        # Salvar gráfico
        os.makedirs("data_quality/charts", exist_ok=True)
        plt.savefig("data_quality/charts/evolucao_qualidade.png")
        print("\nGráfico salvo em data_quality/charts/evolucao_qualidade.png")
        
    except ImportError:
        print("\nPara visualizar gráficos, instale matplotlib: pip install matplotlib")


def criar_documento_validacao():
    """Cria um exemplo de documento de validação para um modelo de ML."""
    # Definir esquema de validação para dados de produção vinícola
    schema = {
        "ano": NumericValidator(
            field_name="ano", 
            min_value=1990, 
            max_value=datetime.now().year, 
            is_integer=True,
            required=True
        ),
        "regiao": DictValidator(
            field_name="regiao",
            schema={
                "nome": StringValidator("nome", min_length=3, required=True),
                "estado": StringValidator("estado", min_length=2, max_length=2, required=True),
                "pais": StringValidator("pais", min_length=3, required=True)
            }
        ),
        "producao": ListValidator(
            field_name="producao",
            item_validator=DictValidator(
                field_name="item",
                schema={
                    "uva": StringValidator("uva", min_length=2, required=True),
                    "quantidade": NumericValidator("quantidade", min_value=0, required=True),
                    "unidade": StringValidator("unidade", allowed_values=["ton", "kg"], required=True)
                }
            ),
            min_length=1
        ),
        "metadata": DictValidator(
            field_name="metadata",
            schema={
                "fonte": StringValidator("fonte", required=True),
                "data_coleta": DateValidator("data_coleta", required=True),
                "versao": StringValidator("versao", required=False)
            },
            required=False
        )
    }
    
    # Criar um validador para documentos completos
    doc_validator = DictValidator(
        field_name="documento",
        schema=schema
    )
    
    # Documento exemplo (válido)
    doc_valido = {
        "ano": 2022,
        "regiao": {
            "nome": "Serra Gaúcha",
            "estado": "RS",
            "pais": "Brasil"
        },
        "producao": [
            {"uva": "Cabernet Sauvignon", "quantidade": 1200.5, "unidade": "ton"},
            {"uva": "Merlot", "quantidade": 850.0, "unidade": "ton"},
            {"uva": "Chardonnay", "quantidade": 650.75, "unidade": "ton"}
        ],
        "metadata": {
            "fonte": "IBGE",
            "data_coleta": "2023-01-15",
            "versao": "1.0"
        }
    }
    
    # Documento com problemas
    doc_invalido = {
        "ano": 1950,  # Ano muito antigo
        "regiao": {
            "nome": "Vale do Vinho",
            "estado": "RGS",  # Estado inválido (deveria ser 2 caracteres)
            "pais": "BR"  # País muito curto
        },
        "producao": [
            {"uva": "Cabernet", "quantidade": 1200.5, "unidade": "ton"},
            {"uva": "Merlot", "quantidade": -850.0, "unidade": "ton"},  # Quantidade negativa
            {"uva": "Chardonnay", "quantidade": 650.75, "unidade": "litros"}  # Unidade inválida
        ],
        "metadata": {
            "fonte": "IBGE",
            "data_coleta": "01/15/2023"  # Formato de data incorreto
        }
    }
    
    # Validar os documentos
    print("=== Validação de Documentos ===")
    
    resultado_valido = doc_validator.validate(doc_valido)
    print(f"\nDocumento válido:")
    print(f"Válido: {resultado_valido.is_valid}")
    print(f"Problemas: {len(resultado_valido.issues)}")
    
    resultado_invalido = doc_validator.validate(doc_invalido)
    print(f"\nDocumento inválido:")
    print(f"Válido: {resultado_invalido.is_valid}")
    print(f"Problemas: {len(resultado_invalido.issues)}")
    
    # Mostrar problemas do documento inválido
    print("\nProblemas encontrados:")
    for issue in resultado_invalido.issues:
        print(f"- {issue}")
        
    # Gerar relatório
    reporter = ValidationReporter("validacao_documento")
    os.makedirs("reports", exist_ok=True)
    reporter.to_json(resultado_invalido, "reports/validacao_documento.json")
    reporter.to_csv(resultado_invalido, "reports/validacao_documento.csv")
    print("\nRelatórios gerados em:")
    print("- reports/validacao_documento.json")
    print("- reports/validacao_documento.csv")


if __name__ == "__main__":
    print("\n=== EXEMPLOS DO SISTEMA DE VALIDAÇÃO DE DADOS ===\n")
    
    print("\n=== 1. Validação de dados simples ===\n")
    exemplo_validacao_dados_simples()
    
    print("\n=== 2. Normalização de dados ===\n")
    exemplo_normalizacao_dados()
    
    print("\n=== 3. Validação de DataFrame ===\n")
    exemplo_validacao_dataframe()
    
    print("\n=== 4. Documento de validação ===\n")
    criar_documento_validacao()
    
    print("\n=== 5. Monitoramento de qualidade de dados ===\n")
    exemplo_monitoramento_qualidade()
    
    # O exemplo de pipeline com validação requer a presença dos arquivos e estruturas do projeto
    # Opcional: Descomente para executar se as dependências estiverem presentes
    # print("\n=== 6. Pipeline com validação ===\n")
    # exemplo_pipeline_com_validacao()
    
    print("\n=== EXEMPLOS CONCLUÍDOS ===\n")
