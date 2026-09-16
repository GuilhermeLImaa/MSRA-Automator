import os
import sys
import shutil
import subprocess

def run():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    print("=== MSRA Automator v2.0.0 Build Script ===")

    # 1. Icons
    py = sys.executable
    print("1/4: Gerando icones...")
    icon_res = subprocess.run([py, "convert_svg_to_ico.py"], cwd=base_dir, capture_output=True, text=True)
    print("Icons output:", icon_res.stdout)

    # 2. PyInstaller
    print("2/4: Compilando executavel com PyInstaller...")
    pyi_res = subprocess.run([py, "-m", "PyInstaller", "--clean", "MSRA Automator.spec"], cwd=base_dir, capture_output=True, text=True)
    print("PyInstaller STDOUT tail:\n", pyi_res.stdout[-800:] if pyi_res.stdout else "")
    if pyi_res.returncode != 0:
        print("PyInstaller STDERR:\n", pyi_res.stderr)
        return False

    # 3. Copy EXE
    dist_exe = os.path.join(base_dir, "dist", "MSRA Automator.exe")
    target_exe = os.path.join(base_dir, "MSRA Automator.exe")
    print("3/4: Organizando executavel final...")
    if os.path.exists(dist_exe):
        shutil.copy2(dist_exe, target_exe)
        size_mb = os.path.getsize(target_exe) / (1024 * 1024)
        print(f"Sucesso! 'MSRA Automator.exe' gerado com {size_mb:.2f} MB")
    else:
        print("ERRO: 'dist/MSRA Automator.exe' nao encontrado!")
        return False

    # 4. Git commit e Tag
    print("4/4: Criando commit e Tag v2.0.0 no Git...")
    subprocess.run(["git", "add", "main.py", "gui/main_window.py", "README.md", "MSRA Automator.exe"], cwd=base_dir)
    subprocess.run(["git", "commit", "-m", "Release v2.0.0 - Compilacao do executavel e versao 2.0.0"], cwd=base_dir)
    subprocess.run(["git", "tag", "-d", "v2.0.0"], cwd=base_dir, capture_output=True)
    tag_res = subprocess.run(["git", "tag", "-a", "v2.0.0", "-m", "Versao 2.0.0 do MSRA Automator"], cwd=base_dir, capture_output=True, text=True)
    print("Git Tag output:", tag_res.stdout, tag_res.stderr)

    tags = subprocess.run(["git", "tag", "-l"], cwd=base_dir, capture_output=True, text=True)
    print("Tags atuais no Git:\n", tags.stdout)
    print("=== RELEASE V2.0.0 COMPLETA ===")
    return True

if __name__ == "__main__":
    run()
