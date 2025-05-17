"""
Utilitários para implementação de HATEOAS.

Este módulo fornece funções para adicionar links hypermedia às respostas da API,
seguindo o princípio HATEOAS (Hypermedia as the Engine of Application State).
"""
from typing import Dict, List, Any, Optional, Union, cast

def add_links(response: Dict[str, Any], resource_path: str, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Adiciona links HATEOAS a uma resposta.
    
    Args:
        response: Resposta a ser enriquecida com links
        resource_path: Caminho do recurso (ex: "production")
        year: Ano do filtro, se aplicável
        
    Returns:
        Resposta com links adicionados
    """
    base_path = f"/api/v1/{resource_path}"
    
    # Links básicos - use simple dictionary without complex type annotations
    links: Dict[str, Any] = {
        "self": {"href": base_path}
    }
    
    # Links específicos por tipo de recurso
    if resource_path == "production":
        links["wine"] = {"href": f"{base_path}/wine"}
        links["grape"] = {"href": f"{base_path}/grape"}
        links["derivative"] = {"href": f"{base_path}/derivative"}
    elif resource_path == "imports":
        links["wine"] = {"href": f"{base_path}/vinhos"}
        links["sparkling"] = {"href": f"{base_path}/espumantes"}
        links["fresh"] = {"href": f"{base_path}/uvas-frescas"}
        links["raisins"] = {"href": f"{base_path}/passas"}
        links["juice"] = {"href": f"{base_path}/suco"}
    elif resource_path == "exports":
        links["wine"] = {"href": f"{base_path}/vinhos"}
        links["sparkling"] = {"href": f"{base_path}/espumantes"}
        links["fresh"] = {"href": f"{base_path}/uvas-frescas"}
        links["juice"] = {"href": f"{base_path}/suco"}
    elif resource_path == "processing":
        links["vinifera"] = {"href": f"{base_path}/vinifera"}
        links["american"] = {"href": f"{base_path}/american"}
        links["table"] = {"href": f"{base_path}/table"}
        links["unclassified"] = {"href": f"{base_path}/unclassified"}
    
    # Add related resource links
    links["related"] = {
        "production": {"href": "/api/v1/production"},
        "imports": {"href": "/api/v1/imports"},
        "exports": {"href": "/api/v1/exports"},
        "processing": {"href": "/api/v1/processing"},
    }
    
    # Adicionar parâmetro de ano se fornecido
    if year is not None:
        # Modify direct links
        for key, link in list(links.items()):
            if key != "related" and isinstance(link, dict) and "href" in link:
                href_value = str(link["href"])
                if "?" in href_value:
                    link["href"] = f"{href_value}&year={year}"
                else:
                    link["href"] = f"{href_value}?year={year}"
        
        # Modify related links
        related = links.get("related")
        if isinstance(related, dict):
            for rel_key, rel_link in related.items():
                if isinstance(rel_link, dict) and "href" in rel_link:
                    href_value = str(rel_link["href"])
                    rel_link["href"] = f"{href_value}?year={year}"
        
        # Adicionar ano anterior e posterior se aplicável
        links["prev_year"] = {"href": f"{base_path}?year={year-1}"}
        links["next_year"] = {"href": f"{base_path}?year={year+1}"}
    
    # Adicionar os links à resposta
    response["_links"] = links
    return response
