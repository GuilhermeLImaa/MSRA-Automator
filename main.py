import sys
import os
import traceback

# Garante que as importações locais e caminhos relativos funcionem
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
os.chdir(base_dir)

def global_exception_handler(exctype, value, tb):
    with open(os.path.join(base_dir, "crash.txt"), "w") as f:
        f.write("".join(traceback.format_exception(exctype, value, tb)))
sys.excepthook = global_exception_handler

try:
    import site
    from core.admin_check import is_admin, run_as_admin

    site_path_file = os.path.join(base_dir, "site_path.txt")

    def create_desktop_shortcut():
        try:
            # Tenta ler caminhos locais antes de importar win32com
            if os.path.exists(site_path_file):
                with open(site_path_file, "r") as f:
                    for line in f:
                        p = line.strip()
                        if p and p not in sys.path:
                            site.addsitedir(p)
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop = shell.SpecialFolders("Desktop")
            shortcut_path = os.path.join(desktop, "MSRA Automator.lnk")
            
            python_exe = sys.executable
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_exe):
                pythonw_exe = python_exe
                
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = pythonw_exe
            shortcut.Arguments = f'"{os.path.join(base_dir, "main.py")}"'
            shortcut.WorkingDirectory = base_dir
            shortcut.IconLocation = pythonw_exe
            shortcut.Description = "Automação MSRA"
            shortcut.save()
        except Exception:
            pass

    if not is_admin():
        # Salva os caminhos de bibliotecas do usuário atual (não-elevado)
        with open(site_path_file, "w") as f:
            for p in sys.path:
                f.write(p + "\n")
            f.write(site.getusersitepackages() + "\n")
        create_desktop_shortcut()
    else:
        # Lê e injeta os caminhos quando elevado, para encontrar o PyQt6 e pywinauto
        if os.path.exists(site_path_file):
            with open(site_path_file, "r") as f:
                for line in f:
                    p = line.strip()
                    if p and p not in sys.path:
                        site.addsitedir(p)
                        # A partir do Python 3.8, as DLLs precisam ser explicitamente adicionadas
                        if hasattr(os, "add_dll_directory") and os.path.isdir(p):
                            try:
                                os.add_dll_directory(p)
                                pywin_sys = os.path.join(p, "pywin32_system32")
                                if os.path.isdir(pywin_sys):
                                    os.add_dll_directory(pywin_sys)
                                win32_dir = os.path.join(p, "win32")
                                if os.path.isdir(win32_dir):
                                    os.add_dll_directory(win32_dir)
                            except Exception:
                                pass

    from PyQt6.QtWidgets import QApplication, QMessageBox
    from core.logger import msra_logger
    from gui.main_window import MainWindow

    def main():
        # 1. Verifica se está elevado
        if not is_admin():
            # 2. Solicita elevação e reinicia
            success = run_as_admin()
            if success:
                # O novo processo foi iniciado com sucesso, encerra este
                sys.exit(0)
            else:
                # Se o usuário recusar o UAC ou falhar, avisa e aborta
                app = QApplication(sys.argv)
                QMessageBox.critical(
                    None, 
                    "Erro de Permissão", 
                    "O MSRA Automator precisa ser executado como Administrador para interagir com os processos do sistema."
                )
                sys.exit(1)

        # 3. Se chegou aqui, já é administrador. Inicia a aplicação normalmente.
        app = QApplication(sys.argv)
        
        # Define fonte global
        font = app.font()
        font.setFamily("Segoe UI")
        app.setFont(font)

        window = MainWindow()
        window.show()

        sys.exit(app.exec())

    if __name__ == "__main__":
        main()
        
except Exception as e:
    with open(os.path.join(base_dir, "crash.txt"), "w") as f:
        f.write("Erro crítico:\n")
        f.write("".join(traceback.format_exception(type(e), e, e.__traceback__)))

