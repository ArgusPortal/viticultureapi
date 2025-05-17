# Melhores Práticas para o Sistema de Validação

Este documento apresenta as melhores práticas para utilização do sistema de validação da VitiBrasil API, com exemplos de código e padrões recomendados.

## 1. Estruturação de Validadores

### 1.1. Campo Único vs. Documento Completo

Para validação de um único campo, use os validadores específicos:

```python
# Validação de um campo simples
validator = StringValidator(
    field_name="nome_vinho",
    min_length=3,
    max_length=50,
    pattern=r'^[a-zA-ZáàâãéèêíóôõúçÁÀÂÃÉÈÍÓÔÕÚÇ\s\-]+$'
)

result = validator.validate("Cabernet Sauvignon")
```

Para validação de documentos complexos, componha validadores usando `DictValidator`:

```python
# Validação de um documento complexo
schema = {
    "produto": StringValidator("produto", min_length=2, required=True),
    "quantidade": NumericValidator("quantidade", min_value=0),
    "data": DateValidator("data", min_date="2020-01-01")
}

validator = DictValidator("pedido", schema=schema)
result = validator.validate({
    "produto": "Vinho Tinto",
    "quantidade": 12,
    "data": "2023-05-20"
})
```

### 1.2. Validações Aninhadas

Para estruturas aninhadas, combine os validadores hierarquicamente:

```python
endereco_schema = {
    "rua": StringValidator("rua", required=True),
    "numero": NumericValidator("numero", is_integer=True),
    "complemento": StringValidator("complemento", required=False)
}

cliente_schema = {
    "nome": StringValidator("nome", min_length=3, required=True),
    "email": StringValidator("email", pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$'),
    "endereco": DictValidator("endereco", endereco_schema)
}

validator = DictValidator("cliente", cliente_schema)
```

## 2. Tratamento de Resultados de Validação

### 2.1. Verificação Simples

```python
result = validator.validate(data)
if result.is_valid:
    # Prosseguir com processamento
    process_data(data)
else:
    # Tratar erros
    handle_validation_errors(result)
```

### 2.2. Tratamento Detalhado de Erros

```python
result = validator.validate(data)

# Separar por severidade
errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
warnings = result.get_issues_by_severity(ValidationSeverity.WARNING)

# Registrar avisos mas continuar
for warning in warnings:
    logger.warning(f"Validação: {warning}")

# Interromper processamento em caso de erros
if errors:
    error_details = [f"{e.field}: {e.message}" for e in errors]
    raise ValidationException(f"Dados inválidos: {', '.join(error_details)}")
```

### 2.3. Geração de Relatórios

```python
from app.core.validation import ValidationReporter

reporter = ValidationReporter("validacao_vinhos")

# Gerar relatório JSON
reporter.to_json(result, "reports/validation/vinhos_report.json")

# Gerar relatório CSV para análise em planilhas
reporter.to_csv(result, "reports/validation/vinhos_report.csv")
```

## 3. Integração com Pipelines

### 3.1. Validação como Etapa do Pipeline

```python
from app.core.validation.pipeline import ValidationPipelineFactory
from app.core.pipeline import Pipeline, CSVExtractor, DataFrameToCSVLoader

# Criar pipeline com validação integrada
pipeline = Pipeline()
pipeline.add_extractor(CSVExtractor("data/raw/vinhos.csv"))
pipeline.add_transformer(ValidationPipelineFactory.create_validating_dataframe_transformer(
    name="validacao_vinhos",
    column_validators={
        'nome': StringValidator('nome', min_length=2),
        'tipo': StringValidator('tipo', allowed_values=["Tinto", "Branco", "Rosé"]),
        'safra': NumericValidator('safra', min_value=1900, max_value=2023)
    },
    fail_on_invalid=False,  # Continuar processamento mesmo com erros
    report_dir="reports/validation"
))
pipeline.add_loader(DataFrameToCSVLoader("data/processed/vinhos_validados.csv"))

# Executar pipeline
result = pipeline.execute()
```

### 3.2. Combinação de Validação e Normalização

```python
# Criar normalizadores para colunas
column_normalizers = {
    'nome': StringNormalizer('nome', strip=True, uppercase=False),
    'tipo': StringNormalizer('tipo', strip=True, uppercase=True),
    'preco': NumericNormalizer('preco', decimal_places=2)
}

# Criar pipeline com normalização após validação
pipeline = Pipeline()
pipeline.add_extractor(extractor)
pipeline.add_transformer(validacao_transformer)  # Primeiro validar
pipeline.add_transformer(ValidationPipelineFactory.create_normalizing_dataframe_transformer(
    name="normalizacao_vinhos",
    column_normalizers=column_normalizers
))  # Depois normalizar
pipeline.add_loader(loader)
```

## 4. Monitoramento da Qualidade de Dados

### 4.1. Configuração do Monitor

```python
from app.core.validation import DataQualityMonitor

# Criar monitor
monitor = DataQualityMonitor(
    name="producao_vinicola",
    storage_dir="data_quality/reports/producao_vinicola"
)

# Registrar resultados de validação com contexto
monitor.record_validation(
    validation_result=result, 
    context={
        "fonte": "scraping",
        "data_ref": "2023-06-15",
        "registros_processados": 1250
    }
)
```

### 4.2. Análise de Tendências

```python
# Obter métricas históricas dos últimos 30 dias
metricas = monitor.get_historical_metrics(days=30)

# Verificar se a qualidade está melhorando
import pandas as pd

df = pd.DataFrame(metricas)
# Calcular média móvel de 7 dias para suavizar flutuações
df['media_movel'] = df['total_issues'].rolling(7).mean()

# Detectar tendência
recent_trend = df['media_movel'].iloc[-7:].mean() < df['media_movel'].iloc[-14:-7].mean()
if recent_trend:
    print("Qualidade dos dados está melhorando")
else:
    print("Qualidade dos dados está estável ou piorando")
```

## 5. Customização de Validadores

### 5.1. Criando um Validador Especializado

Para necessidades específicas, você pode estender a classe base `Validator`:

```python
from app.core.validation import Validator, ValidationResult, ValidationIssue, ValidationSeverity

class CPFValidator(Validator[str]):
    """Validador especializado para CPF brasileiro."""
    
    def __init__(self, field_name: str, required: bool = True):
        self.field_name = field_name
        self.required = required
    
    def validate(self, data: Optional[str]) -> ValidationResult:
        result = ValidationResult()
        
        # Verificar se é None quando obrigatório
        if data is None:
            if self.required:
                result.add_issue(ValidationIssue(
                    field=self.field_name,
                    message="CPF obrigatório não fornecido",
                    severity=ValidationSeverity.ERROR
                ))
            return result
        
        # Remover caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, data))
        
        # Verificar tamanho
        if len(cpf) != 11:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="CPF deve conter 11 dígitos",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
            return result
            
        # Verificar dígitos verificadores (implementação simplificada)
        if cpf == cpf[0] * 11:
            result.add_issue(ValidationIssue(
                field=self.field_name,
                message="CPF inválido (dígitos repetidos)",
                severity=ValidationSeverity.ERROR,
                value=data
            ))
            
        # Implementação completa do algoritmo de validação de CPF...
        
        return result
```

## 6. Recomendações Gerais

1. **Mensagens claras**: Escreva mensagens de erro descritivas que ajudem a identificar o problema
2. **Hierarquia de campos**: Para estruturas aninhadas, use nomes que refletem a hierarquia (ex: `cliente.endereco.rua`)
3. **Validação em camadas**: Comece com validação básica e depois aplique regras de negócio mais complexas
4. **Relatórios periódicos**: Gere relatórios regulares de qualidade de dados para acompanhar tendências
5. **Combine validação e normalização**: Para dados de usuário, normalize antes de validar regras de negócio
6. **Documente validadores**: Mantenha documentação atualizada sobre as regras de validação aplicadas
7. **Evite duplicação**: Reutilize validadores em diferentes contextos usando composição
8. **Testes unitários**: Crie testes específicos para seus validadores com casos de borda

## 7. Tratamento de Valores Nulos e Tipo-Segurança

### 7.1. Verificações Explícitas para Valores Nulos

Para garantir tipo-segurança em Python, especialmente com tipagem estática:

```python
def validate(self, data: Optional[Union[int, float]]) -> ValidationResult:
    # Primeiro faça as validações comuns
    result, should_continue = validate_common(
        data, self.field_name, self.required
    )
    
    if not should_continue:
        return result
        
    # Garantir explicitamente que data não é None antes de usar operadores de comparação
    if data is None:
        return result
    
    # Agora é seguro usar operadores de comparação com data
    if data < 0 and not self.allow_negative:
        result.add_issue(ValidationIssue(
            field=self.field_name,
            message="Valor negativo não permitido",
            severity=ValidationSeverity.ERROR,
            value=data
        ))
```

### 7.2. Verificações de Tipo para Operações Específicas

Para operações que exigem tipos específicos:

```python
# Para strings
if data is not None:
    if not isinstance(data, str):
        result.add_issue(ValidationIssue(
            field=self.field_name,
            message="Valor deve ser uma string",
            severity=ValidationSeverity.ERROR,
            value=data
        ))
    else:
        # Operações seguras com strings
        if self.pattern and not self.pattern.match(data):
            # Validação de padrão regex
```

### 7.3. Lidando com NaN em Validações Numéricas

Valores NaN requerem tratamento especial:

```python
if isinstance(data, float) and pd.isna(data):
    result.add_issue(ValidationIssue(
        field=self.field_name,
        message="Valor numérico contém NaN (não é um número)",
        severity=ValidationSeverity.ERROR,
        value="NaN"
    ))
    return result
```
