import os
import sys
import shutil
import subprocess

def run_step(cmd, desc):
    print(f"\n--- {desc} ---")
    print(f"Comando: {' '.join(cmd)}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=base_dir)
    print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    print("RETCODE:", res.returncode)
    return res.returncode == 0

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=== MSRA Automator v2.0.0 Build Script ===")

    # 1. Gerar ícones a partir de SVG
    py_exe = sys.executable
    if not run_step([py_exe, "convert_svg_to_ico.py"], "Etapa 1: Gerando ícones (.png e .ico)"):
        print("Aviso na geração de ícones. Continuando...")

    # 2. Compilar com PyInstaller
    print("\n--- Etapa 2: Compilando o executável com PyInstaller ---")
    cmd_pyi = [py_exe, "-m", "PyInstaller", "--clean", "MSRA Automator.spec"]
    if not run_step(cmd_pyi, "PyInstaller compilation"):
        print("ERRO CRÍTICO: Falha ao compilar com PyInstaller!")
        sys.exit(1)

    # 3. Copiar executável compilado para a raiz
    dist_exe = os.path.join(base_dir, "dist", "MSRA Automator.exe")
    target_exe = os.path.join(base_dir, "MSRA Automator.exe")

    if os.path.exists(dist_exe):
        exe_size = os.path.getsize(dist_exe)
        print(f"\n--- Etapa 3: Copiando executável ({exe_size} bytes) para a raiz ---")
        shutil.copy2(dist_exe, target_exe)
        print(f"Sucesso! Arquivo 'MSRA Automator.exe' criado na raiz com {os.path.getsize(target_exe)} bytes.")
    else:
        print("ERRO CRÍTICO: 'dist/MSRA Automator.exe' não foi encontrado!")
        sys.exit(1)

    # 4. Operações de Git (commit e tag)
    print("\n--- Etapa 4: Configuração e criação de Tag v2.0.0 no Git ---")
    run_step(["git", "add", "main.py", "gui/main_window.py", "README.md", "MSRA Automator.exe"], "Git Add")
    run_step(["git", "commit", "-m", "Release v2.0.0 - Compilação do executável e atualização de versão"], "Git Commit")
    
    # Remove tag existente se houver para garantir recriação limpa
    subprocess.run(["git", "tag", "-d", "v2.0.0"], capture_output=True, text=True, cwd=base_dir)
    
    if run_step(["git", "tag", "-a", "v2.0.0", "-m", "Versao 2.0.0 do MSRA Automator"], "Git Tag v2.0.0"):
        print("\n==========================================")
        print("SUCCESS: Release v2.0.0 concluída com sucesso!")
        print("Tag 'v2.0.0' criada no Git.")
        print("==========================================")
    else:
        print("AVISO: Falha ao criar a tag no Git.")

if __name__ == "__main__":
    main()
