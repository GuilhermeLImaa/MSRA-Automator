import sys
import os
import traceback
import ctypes

# Garante que as importações locais e caminhos relativos funcionem
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
os.chdir(base_dir)

# Associa o processo ao AppUserModelID do Windows para a barra de tarefas exibir o ícone correto
try:
    myappid = 'ebserh.msra.automator.2.0.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def global_exception_handler(exctype, value, tb):
    traceback.print_exception(exctype, value, tb)
    try:
        with open(os.path.join(base_dir, "crash.txt"), "w", encoding="utf-8") as f:
            f.write("".join(traceback.format_exception(exctype, value, tb)))
    except Exception:
        pass
sys.excepthook = global_exception_handler

try:
    import site
    from core.admin_check import is_admin, run_as_admin

    site_path_file = os.path.join(base_dir, "site_path.txt")

    def create_desktop_shortcut():
        try:
            # Tenta ler caminhos locais antes de importar win32com
            if os.path.exists(site_path_file):
                with open(site_path_file, "r", encoding="utf-8") as f:
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
                
            icon_file = os.path.join(base_dir, "app_icon.ico")
            if not os.path.exists(icon_file):
                icon_file = pythonw_exe

            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = pythonw_exe
            shortcut.Arguments = f'"{os.path.join(base_dir, "main.py")}"'
            shortcut.WorkingDirectory = base_dir
            shortcut.IconLocation = icon_file
            shortcut.Description = "Automação MSRA"
            shortcut.save()
        except Exception:
            pass

    if not is_admin():
        # Salva os caminhos de bibliotecas do usuário atual (não-elevado)
        with open(site_path_file, "w", encoding="utf-8") as f:
            for p in sys.path:
                f.write(p + "\n")
            f.write(site.getusersitepackages() + "\n")
        create_desktop_shortcut()
    else:
        # Lê e injeta os caminhos quando elevado, para encontrar o PyQt6 e pywinauto
        if os.path.exists(site_path_file):
            with open(site_path_file, "r", encoding="utf-8") as f:
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
    from PyQt6.QtGui import QIcon
    from core.logger import msra_logger
    from gui.main_window import MainWindow

    def main():
        # 1. Verifica se está elevado
        if not is_admin():
            # 2. Solicita elevação e reinicia
            print("Solicitando elevação de privilégios de Administrador (UAC)...")
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
        
        # Configura o ícone da aplicação
        icon_path = os.path.join(base_dir, "app_icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_dir, "app_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_dir, "app_icon.svg")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        # Define fonte global
        font = app.font()
        font.setFamily("Segoe UI")
        app.setFont(font)

        window = MainWindow()
        if os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
        window.show()

        sys.exit(app.exec())

    if __name__ == "__main__":
        main()
        
except Exception as e:
    print("❌ Erro crítico ao iniciar o MSRA Automator:")
    traceback.print_exc()
    try:
        with open(os.path.join(base_dir, "crash.txt"), "w", encoding="utf-8") as f:
            f.write("Erro crítico:\n")
            f.write("".join(traceback.format_exception(type(e), e, e.__traceback__)))
    except Exception:
        pass

