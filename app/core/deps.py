from fastapi import Depends
from app.core.security import verify_token

# Dependency para ser usada em todos os endpoints protegidos
def get_current_user(current_user: str = Depends(verify_token)):
    """
    Função de dependência que retorna o usuário atual autenticado.
    
    Essa função deve ser usada de forma consistente em todos os endpoints
    protegidos da API para garantir uniformidade na autenticação.
    """
    return current_user
