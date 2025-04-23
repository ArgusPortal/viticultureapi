"""
Implementação concreta do repositório de arquivos.

Este módulo implementa a interface FileRepository
fornecendo acesso a dados via arquivos locais.
"""
import os
import pandas as pd
import json
import logging
from typing import Dict, List, Any, Optional, Union

from app.repositories.interfaces import FileRepository

logger = logging.getLogger(__name__)

class CSVFileRepository(FileRepository):
    """
    Implementação do repositório para arquivos CSV.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Inicializa o repositório com um diretório base opcional.
        
        Args:
            base_dir: Diretório base para os arquivos. Se None, usa o diretório 'data'
                     na raiz do projeto.
        """
        if base_dir is None:
            self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        else:
            self.base_dir = base_dir
        
        # Garantir que o diretório exista
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Inicializando repositório de arquivos CSV com diretório base: {self.base_dir}")
    
    async def get_data(self, **kwargs) -> Dict[str, Any]:
        """
        Obtém dados de um arquivo CSV.
        
        Args:
            **kwargs: Parâmetros de filtragem, deve incluir 'file_name' ou 'file_path'
            
        Returns:
            Dict com dados e metadados
        """
        file_name = kwargs.get("file_name")
        file_path = kwargs.get("file_path")
        
        if file_path is None and file_name is not None:
            file_path = os.path.join(self.base_dir, file_name)
        
        if file_path is None:
            logger.error("Nenhum arquivo especificado para leitura")
            return {"data": [], "source": "file_not_specified"}
        
        return await self.read_file(file_path, **kwargs)
    
    async def read_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Lê dados de um arquivo CSV.
        
        Args:
            file_path: Caminho para o arquivo
            **kwargs: Parâmetros adicionais como 'sep', 'encoding', etc.
            
        Returns:
            Dict com dados do arquivo e metadados
        """
        if not os.path.exists(file_path):
            logger.warning(f"Arquivo não encontrado: {file_path}")
            return {"data": [], "source": "file_not_found"}
        
        try:
            sep = kwargs.get("sep", ";")
            encoding = kwargs.get("encoding", "utf-8")
            
            df = pd.read_csv(file_path, sep=sep, encoding=encoding)
            
            # Aplicar filtros se especificados
            year = kwargs.get("year")
            if year is not None:
                # Verificar se o ano é uma coluna ou está no cabeçalho
                if str(year) in df.columns:
                    # Ano está no cabeçalho, extrair dados daquela coluna
                    year_data = df[['produto', str(year)]].rename(columns={str(year): 'Quantidade'})
                    year_data['Ano'] = year
                    return {"data": year_data.to_dict('records'), "source": "local_csv"}
                elif 'Ano' in df.columns:
                    # Filtrar por coluna 'Ano'
                    df = df[df['Ano'] == year]
            
            return {
                "data": df.to_dict('records'),
                "source": "csv_file",
                "file_path": file_path,
                "row_count": len(df),
                "columns": df.columns.tolist()
            }
        except Exception as e:
            logger.error(f"Erro ao ler arquivo CSV {file_path}: {str(e)}")
            return {"data": [], "source": "file_error", "error": str(e)}
    
    async def write_file(self, file_path: str, data: Union[pd.DataFrame, List[Dict]], **kwargs) -> bool:
        """
        Escreve dados em um arquivo CSV.
        
        Args:
            file_path: Caminho para o arquivo
            data: DataFrame ou lista de dicionários a serem escritos
            **kwargs: Parâmetros adicionais como 'sep', 'encoding', 'index', etc.
            
        Returns:
            True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            sep = kwargs.get("sep", ";")
            encoding = kwargs.get("encoding", "utf-8")
            index = kwargs.get("index", False)
            
            # Converter para DataFrame se necessário
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = data
            
            # Garantir que o diretório exista
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Escrever o arquivo
            df.to_csv(file_path, sep=sep, encoding=encoding, index=index)
            logger.info(f"Arquivo CSV salvo com sucesso: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao escrever arquivo CSV {file_path}: {str(e)}")
            return False
