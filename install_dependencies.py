import sys
import subprocess
import os

def run_install():
    print("=== Notch Win: Instalador de Dependências ===")
    print("Instalando bibliotecas necessárias para as funções Pro...")
    
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("\n[OK] Todas as dependências foram instaladas com sucesso!")
        print("Agora você pode rodar o main.py normalmente.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] Falha ao instalar dependências: {e}")
    
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Este instalador é destinado apenas para Windows.")
        sys.exit(1)

    run_install()
