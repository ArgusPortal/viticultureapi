"""
Esquemas de validação pré-definidos.

Fornece esquemas de validação reutilizáveis para tipos de dados comuns no projeto.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.validation.validators import (
    StringValidator,
    NumericValidator,
    DateValidator,
    DictValidator,
    ListValidator
)

class ValidationSchemas:
    """
    Esquemas de validação reutilizáveis para tipos comuns de dados.
    
    Esta classe fornece esquemas de validação pré-configurados para formatos 
    de dados frequentemente utilizados no projeto de viticultura.
    """
    
    @staticmethod
    def ano() -> NumericValidator:
        """Validador para anos."""
        return NumericValidator(
            field_name="ano",
            min_value=1900,
            max_value=datetime.now().year,
            is_integer=True,
            required=True
        )
    
    @staticmethod
    def regiao() -> StringValidator:
        """Validador para regiões vitícolas."""
        return StringValidator(
            field_name="regiao",
            min_length=3,
            required=True
        )
    
    @staticmethod
    def uva() -> StringValidator:
        """Validador para tipos de uva."""
        return StringValidator(
            field_name="uva",
            min_length=2,
            required=True
        )
    
    @staticmethod
    def producao_ton() -> NumericValidator:
        """Validador para produção em toneladas."""
        return NumericValidator(
            field_name="producao_ton",
            min_value=0,
            allow_zero=False,
            required=True
        )
    
    @staticmethod
    def area_hectares() -> NumericValidator:
        """Validador para área em hectares."""
        return NumericValidator(
            field_name="area_hectares",
            min_value=0,
            allow_zero=False,
            required=True
        )
    
    @staticmethod
    def valor_monetario(field_name: str = "valor") -> NumericValidator:
        """Validador para valores monetários."""
        return NumericValidator(
            field_name=field_name,
            min_value=0,
            allow_zero=True,
            required=True
        )
    
    @staticmethod
    def data(field_name: str = "data") -> DateValidator:
        """Validador para datas."""
        return DateValidator(
            field_name=field_name,
            min_date="1900-01-01",
            max_date=datetime.now().strftime("%Y-%m-%d"),
            required=True
        )
    
    @staticmethod
    def pais() -> StringValidator:
        """Validador para países."""
        return StringValidator(
            field_name="pais",
            min_length=2,
            required=True
        )
    
    @staticmethod
    def schema_producao() -> Dict[str, Any]:
        """Esquema para dados de produção vinícola."""
        return {
            "ano": ValidationSchemas.ano(),
            "regiao": ValidationSchemas.regiao(),
            "uva": ValidationSchemas.uva(),
            "producao_ton": ValidationSchemas.producao_ton(),
            "area_hectares": ValidationSchemas.area_hectares()
        }
    
    @staticmethod
    def schema_comercializacao() -> Dict[str, Any]:
        """Esquema para dados de comercialização."""
        return {
            "ano": ValidationSchemas.ano(),
            "regiao": ValidationSchemas.regiao(),
            "tipo_produto": StringValidator("tipo_produto", min_length=2, required=True),
            "quantidade": NumericValidator("quantidade", min_value=0, required=True),
            "valor_total": ValidationSchemas.valor_monetario("valor_total"),
            "mercado": StringValidator("mercado", allowed_values=["Interno", "Externo"], required=True)
        }
    
    @staticmethod
    def schema_importacao() -> Dict[str, Any]:
        """Esquema para dados de importação."""
        return {
            "ano": ValidationSchemas.ano(),
            "pais_origem": ValidationSchemas.pais(),
            "produto": StringValidator("produto", min_length=2, required=True),
            "quantidade": NumericValidator("quantidade", min_value=0, required=True),
            "unidade": StringValidator("unidade", min_length=1, required=True),
            "valor_fob": ValidationSchemas.valor_monetario("valor_fob")
        }
    
    @staticmethod
    def schema_exportacao() -> Dict[str, Any]:
        """Esquema para dados de exportação."""
        return {
            "ano": ValidationSchemas.ano(),
            "pais_destino": ValidationSchemas.pais(),
            "produto": StringValidator("produto", min_length=2, required=True),
            "quantidade": NumericValidator("quantidade", min_value=0, required=True),
            "unidade": StringValidator("unidade", min_length=1, required=True),
            "valor_fob": ValidationSchemas.valor_monetario("valor_fob")
        }
    
    @staticmethod
    def schema_processamento() -> Dict[str, Any]:
        """Esquema para dados de processamento de uvas."""
        return {
            "ano": ValidationSchemas.ano(),
            "regiao": ValidationSchemas.regiao(),
            "tipo_processamento": StringValidator("tipo_processamento", min_length=2, required=True),
            "uva": ValidationSchemas.uva(),
            "quantidade": NumericValidator("quantidade", min_value=0, required=True),
            "rendimento": NumericValidator("rendimento", min_value=0, max_value=100, required=False)
        }


def create_validator_from_schema(
    field_name: str, 
    schema: Dict[str, Any], 
    required: bool = True,
    allow_extra_fields: bool = False
) -> DictValidator:
    """
    Cria um validador a partir de um esquema.
    
    Args:
        field_name: Nome do campo principal
        schema: Dicionário com validadores para cada subcampo
        required: Se o campo é obrigatório
        allow_extra_fields: Se permite campos extras não definidos no schema
        
    Returns:
        Validador configurado conforme o esquema fornecido
    """
    return DictValidator(
        field_name=field_name,
        schema=schema,
        required=required,
        allow_extra_fields=allow_extra_fields
    )
