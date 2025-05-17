# Documentação Técnica: Estrutura de Testes

## 1. Visão Geral do Sistema de Testes

A pasta `/tests` contém todos os testes automatizados para a aplicação VitiBrasil API. O sistema de testes foi projetado para garantir a qualidade, estabilidade e robustez da API através de várias camadas de verificação.

### 1.1. Objetivos do Sistema de Testes

- **Verificar funcionalidades**: Garantir que todas as funcionalidades da API funcionem conforme o esperado
- **Prevenir regressões**: Detectar problemas introduzidos por novas mudanças
- **Validar componentes críticos**: Testar especialmente componentes essenciais como cache, middleware e scrapers
- **Verificar tolerância a falhas**: Testar o comportamento do sistema quando ocorrem erros
- **Documentar comportamentos esperados**: Os testes servem como documentação executável do comportamento esperado

### 1.2. Estrutura Geral

Os testes estão organizados por funcionalidade ou componente, seguindo uma convenção de nomenclatura onde os arquivos começam com `test_` para testes unitários/integração e scripts utilitários têm nomes descritivos.

```
/tests/
  ├── test_cache.py           # Testes para o sistema de cache
  ├── test_csv_fallback.py    # Testes para o mecanismo de fallback para CSV
  ├── test_middleware.py      # Testes para os middlewares da API
  ├── test_scraper.py         # Testes para os scrapers de dados
  └── validate_changes.py     # Script para validação manual de alterações
```

## 2. Componentes Principais

### 2.1. Test Cache (`test_cache.py`)

Este arquivo contém testes para o sistema de cache da aplicação, que é um componente crítico para performance.

#### Funcionalidades testadas:
- Armazenamento e recuperação de dados em cache
- Expiração correta de dados após TTL (Time To Live)
- Limpeza manual do cache
- Comportamento em caso de parâmetros diferentes
- Recuperação de informações sobre o estado do cache

#### Principais fixtures e funções:
- `reset_cache_and_counter`: Fixture que limpa o cache antes e depois de cada teste
- `test_cache_hit`: Verifica se o cache armazena e reutiliza resultados corretamente
- `test_cache_expiration`: Verifica a expiração automática de itens no cache
- `test_clear_cache`: Testa a funcionalidade de limpeza manual do cache
- `test_get_cache_info`: Valida as informações retornadas sobre o estado do cache

### 2.2. Test CSV Fallback (`test_csv_fallback.py`)

Testa o mecanismo de fallback para dados locais CSV quando as fontes primárias (como web scraping) falham.

#### Funcionalidades testadas:
- Carregamento correto de arquivos CSV locais
- Fallback automático quando a fonte primária falha
- Manipulação correta de nomes de arquivos diferentes
- Filtragem por ano dos dados carregados
- Comportamento quando arquivos CSV não são encontrados

#### Principais fixtures e funções:
- `test_data_dir`: Cria um diretório temporário com arquivos CSV simulados
- `test_base_scraper_fallback`: Testa o método de fallback diretamente
- `test_production_endpoint_fallback`: Testa o fallback integrado em um endpoint completo

### 2.3. Test Middleware (`test_middleware.py`)

Testa os middlewares da aplicação, especialmente o CacheControlMiddleware.

#### Funcionalidades testadas:
- Adição de cabeçalhos de cache para respostas GET
- Respeito a cabeçalhos de cache personalizados
- Não adição de cabeçalhos para métodos não-GET

#### Testes principais:
- `test_cache_headers_added`: Verifica se cabeçalhos padrão são adicionados
- `test_custom_cache_headers_respected`: Verifica se cabeçalhos personalizados são respeitados
- `test_cache_headers_not_added_for_post`: Verifica comportamento com métodos POST

### 2.4. Test Scraper (`test_scraper.py`)

Testa os scrapers que são responsáveis pela coleta de dados externos.

#### Funcionalidades testadas:
- Extração correta de dados de produção de vinho
- Verificação da estrutura dos dados retornados
- Validação de tipos de dados específicos (como valores numéricos)

#### Testes principais:
- `test_wine_production_scraper`: Valida o scraper de dados de produção de vinho

### 2.5. Script de Validação (`validate_changes.py`)

Este script é usado para validação manual de alterações no sistema, focando especialmente em testar o cache e o sistema de validação de dados.

#### Componentes avaliados:
- Decorator `cache_result`
- Validadores de dados (String, Numeric, Date, etc.)
- DataFrame Validator
- ConcreteCacheLoader no pipeline factory

#### Principais funções:
- `test_cache_decorator`: Testa o funcionamento do decorator de cache
- `test_validators`: Testa os validadores de dados
- `test_pipeline_factory`: Testa o componente ConcreteCacheLoader

## 3. Tecnologias e Ferramentas

### 3.1. Frameworks e Bibliotecas

- **pytest**: Framework principal para execução de testes
- **pytest-asyncio**: Extensão para testar código assíncrono
- **unittest.mock**: Biblioteca para criação de mocks e stubs
- **FastAPI TestClient**: Cliente para testar APIs FastAPI
- **pandas**: Utilizado para manipulação de dados de teste

### 3.2. Padrões e Técnicas

- **Fixtures**: Criação de ambientes controlados para testes
- **Mocking**: Simulação de comportamentos externos
- **Patching**: Substituição temporária de componentes
- **Parametrização**: Execução de testes com diferentes parâmetros
- **Tempo controlado**: Testes que envolvem tempo (como expiração de cache)

## 4. Executando os Testes

### 4.1. Executando todos os testes

```bash
pytest tests/
```

### 4.2. Executando um arquivo de teste específico

```bash
pytest tests/test_cache.py
```

### 4.3. Executando um teste específico

```bash
pytest tests/test_cache.py::test_cache_hit
```

### 4.4. Opções úteis do pytest

- `-v`: Modo verboso
- `-s`: Mostrar saída do console (print statements)
- `--no-header`: Remove o cabeçalho do relatório
- `--no-summary`: Remove o resumo do relatório
- `-xvs`: Modo verboso, para no primeiro erro e mostra saída

### 4.5. Script de validação

O arquivo `validate_changes.py` pode ser executado diretamente para validar alterações:

```bash
python -m tests.validate_changes
```

## 5. Boas Práticas para Contribuições

### 5.1. Estrutura de Testes

- Mantenha os testes organizados por funcionalidade ou componente
- Use nomes descritivos para suas funções de teste
- Documente o propósito de cada teste com docstrings

### 5.2. Garantia de Isolamento

- Utilize fixtures do pytest para configuração e limpeza
- Evite dependências entre testes
- Limpe recursos após cada teste (cache, arquivos temporários, etc.)

### 5.3. Asserções e Validações

- Prefira asserções específicas em vez de asserções genéricas
- Inclua mensagens descritivas nas asserções para facilitar diagnóstico
- Teste tanto casos de sucesso quanto casos de falha

### 5.4. Mocking e Fixtures

- Use mocks para simular dependências externas
- Crie fixtures reutilizáveis para configurações comuns
- Evite mocks desnecessários - use componentes reais quando possível

### 5.5. Testes Assíncronos

- Use `pytest.mark.asyncio` para testes assíncronos
- Certifique-se de que todas as coroutines são devidamente awaited
- Limpe recursos assíncronos corretamente

## 6. Testes Pendentes e Melhorias Futuras

- **Testes de endpoints da API**: Ampliar cobertura para todos os endpoints
- **Testes de autenticação**: Verificar mecanismos de autenticação e autorização
- **Testes de integração**: Expandir testes que verificam a integração entre componentes
- **Testes de performance**: Adicionar testes que verificam o desempenho sob carga
- **CI/CD**: Integrar os testes com pipeline de integração contínua
- **Code coverage**: Implementar relatórios de cobertura de código

## 7. Conclusão

O sistema de testes da VitiBrasil API foi projetado para garantir a qualidade e estabilidade da aplicação. A combinação de testes unitários, de integração e scripts de validação fornece uma cobertura abrangente dos componentes críticos. Ao contribuir para o projeto, certifique-se de seguir as práticas recomendadas e manter ou expandir a cobertura de testes existente.


