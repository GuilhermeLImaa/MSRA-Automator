import ctypes
import sys
import os

def is_admin():
    """Verifica se o script atual está rodando com privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    """Solicita elevação de privilégios e reinicia o script como administrador."""
    if is_admin():
        return True
    
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
    
    try:
        # 1 = Mostrar janela normal, "runas" força o prompt UAC no Windows
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            os.path.dirname(script),
            1
        )
        # Se ret > 32, a elevação foi bem-sucedida e o novo processo iniciou
        return ret > 32
    except Exception:
        return False
