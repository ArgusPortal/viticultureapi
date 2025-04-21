from passlib.context import CryptContext
import sys
import warnings
import bcrypt

# Silenciar o aviso de erro de versão do bcrypt
warnings.filterwarnings("ignore", category=UserWarning)

# Usar a mesma configuração de criptografia da aplicação principal
pwd_context = CryptContext(
    schemes=["bcrypt", "sha256_crypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    sha256_crypt__default_rounds=100000
)

def generate_password_hash(password):
    """Gera hash para a senha usando bcrypt diretamente se necessário"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Usando bcrypt diretamente devido a erro: {str(e)}")
        # Fallback para usar bcrypt diretamente
        salt = bcrypt.gensalt(12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_password_hashes.py senha1 [senha2 senha3 ...]")
        sys.exit(1)
    
    print("\n=== Hashes Gerados para o Arquivo .env ===\n")
    
    for i, password in enumerate(sys.argv[1:], 1):
        hashed = generate_password_hash(password)
        print(f"Senha original: {password}")
        print(f"Hash gerado: {hashed}")
        print(f"\nCopie estas linhas para seu arquivo .env:")
        print(f"USER{i}_USERNAME=seu_usuario{i}@example.com")
        print(f"USER{i}_PASSWORD={hashed}")
        print("\n" + "="*50 + "\n")
