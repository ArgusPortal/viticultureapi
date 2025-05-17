# Detalhamento Técnico da ViticultureAPI

Este documento fornece um detalhamento técnico aprofundado de cada componente da ViticultureAPI, servindo como base para apresentação e avaliação do projeto acadêmico.

## 1. Estrutura da API (`app/api`)

A pasta `api` contém a definição de todos os endpoints da aplicação, organizados em módulos específicos por domínio. Esta estrutura modular facilita a manutenção e escalabilidade do projeto, permitindo adicionar novos endpoints sem afetar os existentes.

### 1.1. Router Principal (`api.py`)

O arquivo `app/api/api.py` atua como ponto central de registro de todos os routers da aplicação. Ele importa os routers individuais de cada módulo de endpoint e os registra no router principal com seus respectivos prefixos.

```python
from fastapi import APIRouter
from app.api.endpoints import processing, exports, imports, production, commercialization, auth, cache, diagnostics

api_router = APIRouter()

# Adicionar routers com descrições mais claras
api_router.include_router(production.router, prefix="/production", tags=["Produção"])
api_router.include_router(processing.router, prefix="/processing", tags=["Processamento"])
api_router.include_router(imports.router, prefix="/imports", tags=["Importação"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exportação"])
api_router.include_router(commercialization.router, prefix="/commercialization", tags=["Comercialização"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(cache.router, prefix="/cache", tags=["Cache"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["Diagnóstico"])
```

Esta abordagem de organização proporciona:

1. **Modularidade**: Cada domínio tem seu próprio módulo de endpoint
2. **Separação clara de responsabilidades**: Cada router atende a uma área específica da aplicação
3. **Documentação por tags**: Endpoints são automaticamente organizados por tags na documentação OpenAPI
4. **Prefixos padronizados**: Todos os endpoints seguem uma convenção clara de URL

### 1.2. Endpoints de Autenticação (`endpoints/auth.py`)

Este módulo implementa o sistema de autenticação baseado em JWT (JSON Web Tokens), oferecendo endpoints para:

1. **Geração de Token**: Endpoint `/auth/token` que recebe credenciais e retorna um token JWT
2. **Autenticação e Teste**: Endpoint `/auth/authenticate` para facilitar testes de autenticação

O sistema utiliza:
- **Biblioteca passlib**: Para hash seguro de senhas
- **python-jose**: Para codificação e decodificação de tokens JWT
- **Variáveis de ambiente**: Para armazenar usuários e senhas em desenvolvimento

```python
@router.post("/token", summary="Obter token de acesso")
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...)
):
    # Verifica credenciais e gera token
```

O módulo também implementa a função `verify_password` para comparação segura de senhas, com múltiplos níveis de fallback para garantir robustez.

### 1.3. Endpoints de Produção (`endpoints/production.py`)

Este módulo fornece dados sobre produção de uvas, vinhos e derivados no Brasil. Estruturado para oferecer:

1. **Dados gerais**: Endpoint base `/production/` para visão geral da produção
2. **Dados de vinhos**: Endpoint `/production/wine` específico para produção vinícola
3. **Dados de uvas**: Endpoint `/production/grape` para produção de uvas
4. **Dados de derivados**: Endpoint `/production/derivative` para outros derivados

Características importantes:
- **Filtros por ano**: Todos os endpoints aceitam um parâmetro `year` opcional
- **Cache de resultados**: Utiliza o decorator `@cache_result` para otimização
- **Fallback para dados locais**: Quando a extração web falha, usa dados em CSV
- **Limpeza de dados**: Remove artefatos de navegação com `clean_navigation_arrows`
- **HATEOAS**: Implementa links hipermídia para navegação entre recursos

O módulo usa o `ProductionScraper` para extrair dados do site VitiBrasil da Embrapa.

### 1.4. Endpoints de Importação (`endpoints/imports.py`)

Este módulo fornece dados detalhados sobre importação de produtos vitivinícolas para o Brasil.

Endpoints principais:
1. **Dados gerais**: `/imports/` - Dados agregados de todos os tipos de importação
2. **Vinhos**: `/imports/vinhos` - Importação específica de vinhos
3. **Espumantes**: `/imports/espumantes` - Importação de vinhos espumantes
4. **Uvas Frescas**: `/imports/uvas-frescas` - Importação de uvas in natura
5. **Uvas Passas**: `/imports/passas` - Importação de uvas passas
6. **Suco de Uva**: `/imports/suco` - Importação de sucos de uva

O módulo implementa uma função `build_api_response` que padroniza as respostas, garantindo formato consistente e tratamento adequado de casos de erro:

```python
def build_api_response(data, year=None):
    # Constrói resposta padronizada a partir dos dados extraídos
    # Trata casos de erro, dados vazios, etc.
```

Características de destaque:
- **Documentação detalhada**: Cada endpoint tem documentação específica
- **Tratamento de exceções**: Uso de try/except com logging detalhado
- **Autenticação**: Todos os endpoints utilizam `verify_token` para autenticação
- **Respostas estruturadas**: Formato consistente com dados, contagem e metadados

### 1.5. Endpoints de Exportação (`endpoints/exports.py`)

Similar ao módulo de importações, este módulo fornece dados sobre exportações brasileiras de produtos vitivinícolas.

Endpoints principais:
1. **Dados gerais**: `/exports/` - Visão consolidada de exportações
2. **Vinhos**: `/exports/vinhos` - Exportação específica de vinhos de mesa
3. **Espumantes**: `/exports/espumantes` - Exportação de espumantes
4. **Uvas Frescas**: `/exports/uvas-frescas` - Exportação de uvas frescas
5. **Suco de Uva**: `/exports/suco` - Exportação de sucos de uva

O módulo segue o mesmo padrão de estrutura e implementação do módulo de importações, com respostas padronizadas e tratamento consistente de erros.

### 1.6. Endpoints de Processamento (`endpoints/processing.py`)

Este módulo fornece dados sobre o processamento industrial de uvas no Brasil, separados por tipo de uva.

Endpoints principais:
1. **Processamento geral**: `/processing/` - Dados gerais de processamento
2. **Uvas viníferas**: `/processing/vinifera` - Processamento de uvas viníferas
3. **Uvas americanas**: `/processing/american` - Processamento de uvas americanas
4. **Uvas de mesa**: `/processing/table` - Processamento de uvas de mesa
5. **Uvas não identificadas**: `/processing/unclassified` - Processamento de uvas sem classificação específica

Os dados apresentam informações sobre quantidades processadas, por variedade e região.

### 1.7. Endpoints de Comercialização (`endpoints/commercialization.py`)

Fornece dados sobre comercialização de vinhos e derivados no mercado interno brasileiro.

```python
@router.get("/", response_model=Dict[str, Any], summary="Dados de comercialização de vinhos")
@cache_result(ttl_seconds_or_func=3600)
async def get_commercialization_data(
    year: Optional[int] = Query(None, description="Filtrar por ano específico"),
    current_user: str = Depends(verify_token)
):
    # Implementação do endpoint
```

O módulo usa o `CommercializationScraper` para obter dados do site VitiBrasil e aplica limpeza aos dados com `clean_navigation_arrows`.

### 1.8. Endpoints de Cache (`endpoints/cache.py`)

Este módulo fornece funcionalidades para gerenciar e monitorar o sistema de cache da aplicação.

Endpoints principais:
1. **Informações do cache**: `/cache/info` - Estatísticas e detalhes do cache atual
2. **Limpeza do cache**: `/cache/clear` - Permite limpar o cache manualmente
3. **Teste de performance**: `/cache/test` - Demonstra a diferença de performance entre chamadas cacheadas e não-cacheadas

O módulo implementa funções de benchmark para comparar o desempenho de requisições com e sem cache, fornecendo métricas úteis para avaliação da eficiência do caching.

### 1.9. Endpoints de Diagnóstico (`endpoints/diagnostics.py`)

Este módulo fornece ferramentas para diagnóstico e monitoramento da aplicação.

Endpoints principais:
1. **Logs recentes**: `/diagnostics/logs` - Exibe os logs mais recentes da aplicação
2. **Erros recentes**: `/diagnostics/errors` - Filtra apenas entradas de log de nível ERROR
3. **Rotas da aplicação**: `/diagnostics/routes` - Lista todas as rotas registradas
4. **Dependências**: `/diagnostics/dependencies` - Lista pacotes Python instalados
5. **Teste de erros**: `/diagnostics/test-error` - Permite testar o sistema de tratamento de exceções

O módulo é especialmente útil para:
- Monitoramento da saúde da aplicação
- Depuração de problemas em ambiente de produção
- Verificação de configuração e dependências
- Testes de robustez do sistema de tratamento de erros

```python
@router.get("/logs", summary="Logs recentes")
async def get_recent_logs(
    lines: int = Query(100, ge=1, le=1000, description="Número de linhas para retornar"),
    level: str = Query("INFO", description="Nível mínimo de log"),
    current_user: str = Depends(verify_token)
):
    # Implementação para obter e filtrar logs recentes
```

## 2. Implementação HATEOAS

A API implementa o princípio HATEOAS (Hypermedia as the Engine of Application State), elevando-a ao nível 3 de maturidade REST:

1. Cada resposta inclui links relevantes na propriedade `_links`
2. Os links permitem navegação intuitiva entre recursos relacionados  
3. O cliente não precisa conhecer a estrutura de URLs, apenas seguir os links fornecidos

O módulo `core/hypermedia.py` implementa esta funcionalidade, adicionando automaticamente:
- Link para o próprio recurso (`self`)
- Links para recursos relacionados
- Links para subitens específicos
- Links de navegação temporal (ano anterior/posterior)

Esta implementação permite que a API seja verdadeiramente RESTful, com recursos auto-descritivos e descobríveis.
