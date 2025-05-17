# Detalhamento Técnico: Repositories

Este documento detalha a implementação da camada de repositórios da ViticultureAPI, responsável pelo acesso a dados e abstração de fontes de informação.

## 1. Interfaces de Repositório (`app/repositories/interfaces.py`)

Este módulo define interfaces abstratas que estabelecem contratos para as implementações concretas de repositórios:

```python
class FileRepository(ABC):
    """Interface para repositórios que acessam arquivos."""
    
    @abstractmethod
    def read_csv(self, file_path: str) -> Dict[str, Any]:
        """Lê dados de um arquivo CSV."""
        pass
    
    @abstractmethod
    def write_csv(self, file_path: str, data: Any) -> bool:
        """Escreve dados em um arquivo CSV."""
        pass

class ScrapingRepository(ABC):
    """Interface para repositórios que extraem dados via web scraping."""
    
    @abstractmethod
    def extract_table(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extrai tabela de uma página web."""
        pass
    
    @abstractmethod
    def extract_data(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extrai dados genéricos de uma página web."""
        pass
```

A definição de interfaces:
1. Estabelece um contrato claro para implementações
2. Facilita a substituição de implementações (princípio de Liskov)
3. Permite mock objects em testes unitários
4. Melhora a manutenibilidade com baixo acoplamento

## 2. Repositório de Arquivos (`app/repositories/file_repository.py`)

Implementa a interface `FileRepository` para manipulação de arquivos estruturados (CSV, Excel, etc.):

```python
class CSVFileRepository(FileRepository):
    """Implementação concreta para manipulação de arquivos CSV."""
    
    def read_csv(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Lê dados de um arquivo CSV e retorna como dicionário estruturado.
        
        Args:
            file_path: Caminho para o arquivo CSV
            **kwargs: Argumentos opcionais para pandas.read_csv
            
        Returns:
            Dicionário com dados e metadados do arquivo
        """
        try:
            # Definir opções padrão
            options = {
                "encoding": "utf-8",
                "delimiter": ";",
                "decimal": ",",
                "thousands": ".",
                "na_values": ["", "NA", "N/A", "null", "NULL", "-"]
            }
            
            # Sobrescrever com opções fornecidas
            options.update(kwargs)
            
            # Verificar se arquivo existe
            if not os.path.exists(file_path):
                logger.error(f"Arquivo não encontrado: {file_path}")
                return {
                    "data": [],
                    "error": f"Arquivo não encontrado: {file_path}",
                    "source": "file_error"
                }
            
            # Ler CSV com pandas
            df = pd.read_csv(file_path, **options)
            
            # Converter para lista de dicionários
            data = df.to_dict('records')
            
            return {
                "data": data,
                "source": "file",
                "source_file": file_path,
                "rows": len(data),
                "columns": list(df.columns)
            }
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo CSV {file_path}: {str(e)}", exc_info=True)
            return {
                "data": [],
                "error": f"Erro ao ler arquivo: {str(e)}",
                "source": "file_error"
            }
    
    def write_csv(self, file_path: str, data: Any, **kwargs) -> bool:
        """
        Escreve dados em um arquivo CSV.
        
        Args:
            file_path: Caminho para o arquivo CSV
            data: DataFrame ou lista de dicionários para salvar
            **kwargs: Argumentos opcionais para pandas.to_csv
            
        Returns:
            True se operação foi bem-sucedida, False caso contrário
        """
        try:
            # Definir opções padrão
            options = {
                "encoding": "utf-8",
                "index": False,
                "delimiter": ";",
                "decimal": ","
            }
            
            # Sobrescrever com opções fornecidas
            options.update(kwargs)
            
            # Verificar tipo de dados e converter para DataFrame se necessário
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if "data" in data and isinstance(data["data"], list):
                    df = pd.DataFrame(data["data"])
                else:
                    df = pd.DataFrame([data])
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                raise ValueError(f"Tipo de dados não suportado: {type(data)}")
            
            # Criar diretório pai se não existir
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Salvar como CSV
            df.to_csv(file_path, **options)
            
            logger.info(f"Dados salvos com sucesso em {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao escrever arquivo CSV {file_path}: {str(e)}", exc_info=True)
            return False
```

Características importantes:
- **Tratamento robusto de erros**: Exceções capturadas e convertidas em formatos padronizados
- **Flexibilidade de configuração**: Aceita parâmetros adicionais via kwargs
- **Verificação de existência**: Valida se arquivos existem antes de tentar operações
- **Conversão automática**: Suporta diferentes formatos de entrada (DataFrame, dicionários, listas)

## 3. Repositório de Scraping (`app/repositories/scraping_repository.py`)

Implementa a interface `ScrapingRepository` para extração de dados de fontes web:

```python
class BaseScrapingRepository(ScrapingRepository):
    """Implementação base para scraping de dados."""
    
    def __init__(self):
        """Inicializa o repositório com uma sessão HTTP configurada."""
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Cria e configura uma sessão HTTP com retry.
        
        Returns:
            Sessão HTTP configurada
        """
        session = requests.Session()
        
        # Configurar retry para maior robustez
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Adicionar adapter com retry à sessão
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        
        # Configurar User-Agent para evitar bloqueios
        session.headers.update({
            "User-Agent": "ViticultureAPI/1.0 (Academic Research Project; contact@example.org)"
        })
        
        return session
    
    def extract_table(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extrai tabela HTML de uma página web.
        
        Args:
            url: URL da página
            params: Parâmetros de consulta
            
        Returns:
            Dicionário com dados extraídos da tabela
        """
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Usar BeautifulSoup para parsear HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Encontrar todas as tabelas na página
            tables = soup.find_all("table")
            
            if not tables:
                logger.warning("Tabela não encontrada na página")
                return {
                    "data": [],
                    "error": "Tabela não encontrada na página",
                    "source": "scraping_error",
                    "source_url": response.url
                }
                
            # Extrair dados da tabela mais relevante
            best_table = self._find_best_table(tables)
            
            if not best_table:
                logger.warning("Não foi possível determinar tabela adequada")
                return {
                    "data": [],
                    "error": "Não foi possível determinar tabela adequada",
                    "source": "scraping_error",
                    "source_url": response.url
                }
            
            # Extrair dados da melhor tabela
            data = self._extract_table_data(best_table)
            
            return {
                "data": data,
                "source": "web_scraping",
                "source_url": response.url,
                "rows": len(data)
            }
            
        except requests.RequestException as e:
            logger.error(f"Erro na requisição HTTP para {url}: {str(e)}")
            return {
                "data": [],
                "error": f"Erro na requisição HTTP: {str(e)}",
                "source": "scraping_error",
                "source_url": url
            }
        except Exception as e:
            logger.error(f"Erro ao extrair tabela de {url}: {str(e)}", exc_info=True)
            return {
                "data": [],
                "error": f"Erro ao extrair dados: {str(e)}",
                "source": "scraping_error",
                "source_url": url
            }
    
    def _find_best_table(self, tables: List[Any]) -> Optional[Any]:
        """
        Identifica a tabela mais relevante entre as encontradas.
        
        Implementa um algoritmo de pontuação que considera fatores como:
        - Número de linhas e colunas
        - Presença de cabeçalhos
        - Estrutura dos dados
        
        Args:
            tables: Lista de elementos table encontrados
            
        Returns:
            Tabela mais relevante ou None se nenhuma adequada
        """
        # Implementação do algoritmo de pontuação
        best_table = None
        best_score = 0
        
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) <= 1:  # Tabelas com apenas cabeçalho ou vazias
                continue
                
            # Calcular pontuação
            score = len(rows) * 2  # Mais linhas = melhor
            
            # Verificar cabeçalhos (th)
            headers = table.find_all("th")
            if headers:
                score += len(headers) * 3  # Presença de cabeçalhos é bom sinal
            
            # Analisar estrutura da tabela
            cells_per_row = [len(row.find_all(["td", "th"])) for row in rows]
            if cells_per_row and all(count == cells_per_row[0] for count in cells_per_row):
                score += 10  # Estrutura consistente é indicador forte
            
            # Verificar conteúdo
            if any("Total" in str(row) for row in rows):
                score += 5  # Tabelas com totais são normalmente de dados
            
            if score > best_score:
                best_score = score
                best_table = table
        
        return best_table
    
    def _extract_table_data(self, table: Any) -> List[Dict[str, Any]]:
        """
        Extrai dados estruturados de uma tabela HTML.
        
        Args:
            table: Elemento table do BeautifulSoup
            
        Returns:
            Lista de dicionários com os dados da tabela
        """
        rows = table.find_all("tr")
        
        # Extrair cabeçalhos
        header_row = rows[0]
        headers = []
        for header in header_row.find_all(["th", "td"]):
            # Limpar e normalizar texto do cabeçalho
            header_text = self._clean_text(header.get_text(strip=True))
            if not header_text:  # Se estiver vazio, usar placeholder
                header_text = f"Coluna_{len(headers) + 1}"
            headers.append(header_text)
        
        logger.info(f"Found headers: {headers}")
        
        # Extrair dados das linhas
        data = []
        for row in rows[1:]:  # Pular cabeçalho
            cells = row.find_all(["td", "th"])
            
            # Verificar se número de células corresponde ao de cabeçalhos
            if len(cells) != len(headers):
                logger.warning(f"Row has {len(cells)} cells, expected {len(headers)}. Row data: {[cell.get_text(strip=True) for cell in cells]}")
                
                # Se muito diferente, pular linha
                if len(cells) < len(headers) / 2 or len(cells) > len(headers) * 2:
                    continue
            
            # Criar dicionário com dados da linha
            row_data = {}
            for i, cell in enumerate(cells):
                if i >= len(headers):
                    # Mais células que cabeçalhos, usar cabeçalho genérico
                    key = f"Coluna_Extra_{i - len(headers) + 1}"
                else:
                    key = headers[i]
                
                # Limpar e converter texto da célula
                cell_text = self._clean_text(cell.get_text(strip=True))
                row_data[key] = self._convert_value(cell_text)
            
            # Preencher dados faltantes
            for header in headers:
                if header not in row_data:
                    row_data[header] = None
            
            data.append(row_data)
        
        logger.info(f"Extracted {len(data)} rows of data")
        
        # Limpeza adicional dos dados
        cleaned_data = self._clean_data(data)
        logger.info(f"After cleaning: {len(cleaned_data)} rows of data")
        
        return cleaned_data
    
    def _clean_text(self, text: str) -> str:
        """
        Limpa e normaliza texto extraído.
        
        Args:
            text: Texto a ser limpo
            
        Returns:
            Texto limpo
        """
        # Remover múltiplos espaços
        text = re.sub(r'\s+', ' ', text)
        
        # Remover caracteres especiais problemáticos
        text = text.replace('\xa0', ' ').strip()
        
        return text
    
    def _convert_value(self, value: str) -> Any:
        """
        Tenta converter valor para tipo apropriado.
        
        Args:
            value: Valor a converter
            
        Returns:
            Valor convertido ou string original
        """
        # Tentar converter para número
        try:
            # Verificar se é número com vírgula decimal
            if re.match(r'^-?\d+,\d+$', value):
                return float(value.replace(',', '.'))
            
            # Verificar se é número com ponto decimal
            if re.match(r'^-?\d+\.\d+$', value):
                return float(value)
                
            # Verificar se é número inteiro
            if re.match(r'^-?\d+$', value):
                return int(value)
        except ValueError:
            pass
        
        # Retornar valor original se não for número
        return value
    
    def _clean_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpa e padroniza dados extraídos.
        
        Args:
            data: Lista de dicionários com dados
            
        Returns:
            Dados limpos e normalizados
        """
        # Remover linhas vazias
        data = [row for row in data if any(value for value in row.values() if value)]
        
        # Padronizar nomes de colunas
        for row in data:
            # Criar cópia para evitar erro de modificação durante iteração
            keys = list(row.keys())
            
            for key in keys:
                # Normalizar chave
                new_key = key.strip().title()
                
                # Se chave mudou, atualizar dicionário
                if new_key != key:
                    row[new_key] = row.pop(key)
        
        return data
    
    def extract_data(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extrai dados genéricos de uma página web.
        
        Args:
            url: URL da página
            params: Parâmetros de consulta
            
        Returns:
            Dicionário com dados extraídos
        """
        # Por padrão, usa extract_table com seletor padrão
        return self.extract_table(url, params)
```

Características importantes:
1. **Sessão HTTP Robusta**:
   - Implementa retry com backoff exponencial
   - Configura timeouts adequados
   - Define User-Agent para identificação

2. **Algoritmo de Seleção de Tabelas**:
   - Analisa múltiplas tabelas e escolhe a mais relevante
   - Pontuação baseada em características estruturais
   - Adaptável a diferentes layouts de páginas

3. **Extração e Normalização de Dados**:
   - Extração estruturada mantendo relação cabeçalho-dados
   - Limpeza e normalização de texto
   - Conversão automática de tipos de dados
   - Tratamento de inconsistências (diferentes números de células)

4. **Tratamento de Erros**:
   - Captura e registra exceções em diferentes níveis
   - Respostas padronizadas com informações de erro
   - Logging detalhado para diagnóstico

## 4. Repositórios Especializados

Além dos repositórios base, o sistema implementa repositórios especializados para domínios específicos:

### 4.1. Repositório de Produção (`app/repositories/production_repository.py`)

```python
class ProductionRepository(BaseScrapingRepository):
    """Repositório especializado para dados de produção vinícola."""
    
    def __init__(self, base_url: str = "http://vitibrasil.cnpuv.embrapa.br/"):
        super().__init__()
        self.base_url = base_url
        self.file_repository = CSVFileRepository()
    
    def get_production_data(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém dados gerais de produção vinícola.
        
        Args:
            year: Ano específico para filtrar dados
            
        Returns:
            Dicionário com dados de produção
        """
        params = {
            "opcao": "opt_02",
            "subopcao": "subopt_00"
        }
        
        # Adicionar ano se fornecido
        if year is not None:
            params["ano"] = year
        
        # Tentar obter dados via scraping
        result = self.extract_table(f"{self.base_url}/index.php", params)
        
        # Se falhar, tentar carregar de arquivo CSV
        if not result.get("data") or "error" in result:
            logger.info(f"Scraping falhou, tentando arquivo CSV para produção ano={year}")
            
            # Determinar arquivo correto
            file_path = os.path.join(
                "data", 
                "production", 
                f"production_{year}.csv" if year else "production_all.csv"
            )
            
            # Carregar de CSV
            csv_result = self.file_repository.read_csv(file_path)
            
            # Se arquivo existir, usar seus dados
            if not "error" in csv_result:
                return csv_result
        
        return result
    
    # Outros métodos especializados...
```

### 4.2. Repositório de Importação (`app/repositories/imports_repository.py`)

```python
class ImportsRepository(BaseScrapingRepository):
    """Repositório especializado para dados de importação."""
    
    def __init__(self, base_url: str = "http://vitibrasil.cnpuv.embrapa.br/"):
        super().__init__()
        self.base_url = base_url
        self.file_repository = CSVFileRepository()
    
    def get_imports_data(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém dados gerais de importação.
        
        Args:
            year: Ano específico para filtrar dados
            
        Returns:
            Dicionário com dados de importação
        """
        # Primeiro tentar arquivo CSV
        file_path = os.path.join(
            "data", 
            "imports", 
            f"imports_{year}.csv" if year else "imports_all.csv"
        )
        
        csv_result = self.file_repository.read_csv(file_path)
        if not "error" in csv_result:
            return csv_result
            
        # Se arquivo não existir, tentar scraping
        params = {
            "opcao": "opt_01",
            "subopcao": "subopt_00"
        }
        
        if year is not None:
            params["ano"] = year
        
        # A subopt_00 tipicamente não funciona bem para imports, então
        # combinar resultados das subopts específicas
        combined_data = []
        
        # Obter dados de cada subcategoria
        for subopt in ["01", "02", "03", "04", "05"]:
            sub_params = params.copy()
            sub_params["subopcao"] = f"subopt_{subopt}"
            
            result = self.extract_table(f"{self.base_url}/index.php", sub_params)
            
            if result.get("data"):
                # Adicionar campo de categoria
                category_map = {
                    "01": "vinhos",
                    "02": "espumantes",
                    "03": "uvas_frescas",
                    "04": "passas",
                    "05": "sucos"
                }
                
                category = category_map.get(subopt, "outros")
                
                for item in result["data"]:
                    item["categoria"] = category
                    combined_data.append(item)
        
        # Retornar dados combinados
        return {
            "data": combined_data,
            "source": "web_scraping_combined",
            "source_url": self.base_url
        }
    
    # Outros métodos especializados...
```

## 5. Padrão de Projeto Repository

A implementação segue o padrão de projeto Repository, que:

1. **Abstrai Acesso a Dados**: Separa lógica de negócio da lógica de acesso a dados
2. **Centraliza Lógica de Acesso**: Agrupa regras de acesso em uma única classe
3. **Facilita Teste Unitário**: Permite mock objects para testar componentes isolados
4. **Promove Desacoplamento**: Minimiza dependência entre camadas
5. **Padroniza Respostas**: Formato consistente facilita integração com serviços

### Benefícios na ViticultureAPI:

1. **Mecanismo de Fallback**: Se scraping web falha, tenta arquivos CSV
2. **Dados Consistentes**: Estrutura padronizada independente da fonte
3. **Robustez**: Tratamento de erros em múltiplos níveis
4. **Extensibilidade**: Fácil adicionar novas fontes de dados
5. **Manutenibilidade**: Isolamento de mudanças em fontes externas

## 6. Integração com Serviços

Os repositórios são consumidos pela camada de serviço, que:

1. **Adiciona Lógica de Negócio**: Transforma e agrega dados
2. **Aplica Validação**: Valida dados extraídos
3. **Implementa Cache**: Armazena resultados para evitar requisições repetidas
4. **Formata Respostas**: Adapta dados para modelos de resposta da API

O design em camadas (API → Serviço → Repositório → Fonte) permite manutenção de cada nível independentemente.
