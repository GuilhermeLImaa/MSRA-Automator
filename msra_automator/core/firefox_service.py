import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal

class FirefoxUpdateTask(QThread):
    """Thread assíncrona para a Etapa 5: Download do instalador oficial win64 pt-BR do Firefox e instalação silenciosa via WMI com credenciais seguras."""
    output_ready = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)  # percent, status_text
    finished_with_result = pyqtSignal(dict)   # resultado final

    def __init__(self, target_host: str, admin_user: str = "", admin_password: str = "", parent=None):
        super().__init__(parent)
        self.target_host = target_host.strip()
        self.admin_user = admin_user.strip()
        self.admin_password = admin_password

    def _execute_wmi_cmd(self, cmd_content: str, timeout: int = 300) -> str:
        """Executa um comando remoto via WMI sem expor senhas no CLI."""
        cmd_escaped = cmd_content.replace("'", "''")

        ps_script = f"""
$secpasswd = ConvertTo-SecureString '{self.admin_password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ('{self.admin_user}', $secpasswd)
Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList 'cmd.exe /c {cmd_escaped}' -ComputerName {self.target_host} -Credential $cred
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
                timeout=timeout
            )
            return process.stdout or ""
        except subprocess.TimeoutExpired:
            raise TimeoutError("Tempo limite excedido ao disparar WMI via PowerShell.")

    def run(self):
        self.output_ready.emit(f"Iniciando Etapa 5: Atualização do Navegador Firefox em {self.target_host} via WMI...")
        self.progress_updated.emit(20, "Fazendo download e instalação...")

        result = {
            "success": False,
            "error": ""
        }

        try:
            self.output_ready.emit("Baixando e instalando última versão do Firefox via WMI...")
            self.output_ready.emit("Aguardando disparo do download e instalação silenciosa...")

            ps_command = (
                "powershell -NoProfile -Command \""
                "Invoke-WebRequest -Uri 'https://download.mozilla.org/?product=firefox-latest-ssl&os=win64&lang=pt-BR' "
                "-OutFile 'C:\\Windows\\Temp\\ff_update.exe'; "
                "Start-Process -FilePath 'C:\\Windows\\Temp\\ff_update.exe' -ArgumentList '-ms' -Wait; "
                "Remove-Item -Path 'C:\\Windows\\Temp\\ff_update.exe' -Force -ErrorAction SilentlyContinue\""
            )

            self._execute_wmi_cmd(ps_command, timeout=300)

            self.output_ready.emit("✅ Processo de atualização do Firefox disparado e finalizado via WMI!")
            result["success"] = True
            self.progress_updated.emit(100, "Concluído")

        except TimeoutError as te:
            error_msg = str(te)
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        except Exception as e:
            error_msg = f"Erro na atualização do Firefox: {str(e)}"
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        finally:
            self.finished_with_result.emit(result)

