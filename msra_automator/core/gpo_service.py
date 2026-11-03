import subprocess
import os
import time
from PyQt6.QtCore import QThread, pyqtSignal


class GPOTask(QThread):
    """Thread assíncrona para execução remota do comando 'gpupdate /force' via WMI com credenciais seguras."""
    finished = pyqtSignal(str)

    def __init__(self, target_host: str, admin_user: str = "", admin_password: str = "", parent=None):
        super().__init__(parent)
        self.target_host = target_host.strip()
        self.admin_user = admin_user.strip()
        self.admin_password = admin_password

    def run(self):
        temp_filename = "gpo_log.txt"
        unc_path = f"\\\\{self.target_host}\\c$\\Windows\\Temp\\{temp_filename}"
        remote_log_path = f"C:\\Windows\\Temp\\{temp_filename}"

        # Garante que não haja arquivo residual antigo no destino UNC
        if os.path.exists(unc_path):
            try:
                os.remove(unc_path)
            except Exception:
                pass

        # Comando remoto WMI conforme especificação
        cmd_to_run = f'cmd.exe /c "gpupdate /force > {remote_log_path} 2>&1"'
        cmd_escaped = cmd_to_run.replace("'", "''")

        # Injeção de credenciais via PowerShell stdin (sem rastros no CLI)
        ps_script = f"""
$secpasswd = ConvertTo-SecureString '{self.admin_password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ('{self.admin_user}', $secpasswd)
Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList '{cmd_escaped}' -ComputerName {self.target_host} -Credential $cred
"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            process = subprocess.run(
                ['powershell', '-NoProfile', '-Command', '-'],
                input=ps_script,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                timeout=30
            )
        except Exception as e:
            self.finished.emit(f"Erro ao disparar WMI via PowerShell: {str(e)}")
            return

        # Loop de validação e leitura com timeout de 120 segundos
        start_time = time.time()
        timeout = 120
        file_found = False

        while time.time() - start_time < timeout:
            if self.isInterruptionRequested():
                self.finished.emit("Execução abortada pelo operador.")
                return

            if os.path.exists(unc_path) and os.path.getsize(unc_path) > 0:
                file_found = True
                time.sleep(1.5)  # Breve pausa para garantir a finalização da gravação pelo cmd.exe
                break

            time.sleep(1)

        if not file_found or not os.path.exists(unc_path):
            self.finished.emit("Timeout de 120 segundos excedido aguardando o arquivo de log remoto da GPO.")
            return

        # Leitura do texto retornado pelo gpupdate /force
        output_content = ""
        try:
            for enc in ['utf-16', 'utf-8', 'cp850', 'latin1']:
                try:
                    with open(unc_path, 'r', encoding=enc) as f:
                        output_content = f.read()
                    if output_content.strip():
                        break
                except Exception:
                    continue
        except Exception as e:
            output_content = f"Erro ao ler o arquivo de log remoto: {str(e)}"
        finally:
            # Remoção do arquivo .txt remoto via os.remove
            try:
                if os.path.exists(unc_path):
                    os.remove(unc_path)
            except Exception:
                pass

        if not output_content.strip():
            output_content = "O comando gpupdate /force foi executado, porém nenhum conteúdo de log foi gerado."

        self.finished.emit(output_content.strip())
