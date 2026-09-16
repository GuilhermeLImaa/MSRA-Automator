import subprocess
import os
import time
import base64
import re
from PyQt6.QtCore import QThread, pyqtSignal

class ServicesAndUpdatesTask(QThread):
    """Thread assíncrona para a Etapa 6: Desativação de apps de inicialização, processos em 2º plano e disparo do Windows Update via WMI em memória (Base64)."""
    output_ready = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)  # percent, status_text
    finished_with_result = pyqtSignal(dict)   # resultado final

    def __init__(self, target_host: str, target_user: str, admin_user: str = "", admin_password: str = "", parent=None):
        super().__init__(parent)
        self.target_host = target_host.strip()
        self.target_user = target_user.strip()
        self.admin_user = admin_user.strip()
        self.admin_password = admin_password

    def run(self):
        self.output_ready.emit(f"Iniciando Etapa 6: Otimização de Serviços & Updates em {self.target_host} via WMI...")
        self.progress_updated.emit(10, "Em Execução")

        result = {
            "success": False,
            "error": ""
        }

        # Tratamento do nome de usuário
        clean_user = self.target_user.split('\\')[-1].strip()
        match = re.search(r'\(([^)]+)\)', clean_user)
        if match:
            inside = match.group(1)
            users_list = [u.strip() for u in inside.split(',') if u.strip()]
            if users_list:
                clean_user = users_list[0]
        clean_user = clean_user.replace("Múltiplos", "").replace("multiplos", "").strip()

        unc_path = f"\\\\{self.target_host}\\c$\\Windows\\Temp\\step6_done.txt"
        remote_file = f"C:\\Windows\\Temp\\step6_done.txt"

        if os.path.exists(unc_path):
            try:
                os.remove(unc_path)
            except Exception:
                pass

        try:
            self.output_ready.emit("Gerando payload codificado em Base64 para execução remota...")

            ps_payload = f"""
$usuario = "{clean_user}"
$sid = (Get-WmiObject Win32_UserProfile | Where-Object {{ $_.LocalPath -match "\\\\$usuario$" }}).SID
if ($sid) {{
    $runPath = "Registry::HKEY_USERS\\$sid\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
    if (Test-Path $runPath) {{
        Remove-ItemProperty -Path $runPath -Name "com.squirrel.Teams.Teams", "Skype", "OneDrive", "Spotify", "Cortana", "Webex", "WebexHost" -ErrorAction SilentlyContinue
    }}
    $bgPath = "Registry::HKEY_USERS\\$sid\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications"
    if (-not (Test-Path $bgPath)) {{ New-Item -Path $bgPath -Force | Out-Null }}
    Set-ItemProperty -Path $bgPath -Name "GlobalUserDisabled" -Value 1 -Force
    
    Start-Process "UsoClient.exe" -ArgumentList "StartScan" -WindowStyle Hidden
    echo "OK" > {remote_file}
}}
"""
            encoded_payload = base64.b64encode(ps_payload.encode('utf-16le')).decode('utf-8')

            outer_script = f"""
$secpasswd = ConvertTo-SecureString '{self.admin_password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ('{self.admin_user}', $secpasswd)
$comandoWMI = "powershell.exe -NoProfile -EncodedCommand {encoded_payload}"
Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList $comandoWMI -ComputerName {self.target_host} -Credential $cred
"""
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.output_ready.emit("Disparando comando WMI em memória na máquina remota...")
            process = subprocess.run(
                ['powershell', '-NoProfile', '-Command', '-'],
                input=outer_script,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                timeout=45
            )

            # Aguardar confirmação de conclusão via UNC path
            start_time = time.time()
            max_wait = 18
            done = False
            while time.time() - start_time < max_wait:
                if os.path.exists(unc_path) and os.path.getsize(unc_path) > 0:
                    time.sleep(0.5)
                    done = True
                    break
                time.sleep(0.5)

            if not done:
                raise Exception("Tempo limite excedido aguardando o arquivo step6_done.txt via UNC.")

            # Leitura de validação e remoção do arquivo remoto
            try:
                if os.path.exists(unc_path):
                    os.remove(unc_path)
            except Exception:
                pass

            self.output_ready.emit("✅ Apps da inicialização desativados.")
            self.output_ready.emit("✅ Processos em 2º plano bloqueados.")
            self.output_ready.emit("✅ Varredura do Windows Update (UsoClient.exe) iniciada silenciosamente.")
            self.output_ready.emit("✨ Etapa 6 de Serviços e Updates concluída com sucesso!")

            result["success"] = True
            self.progress_updated.emit(100, "Concluído")

        except subprocess.TimeoutExpired:
            error_msg = "Tempo limite excedido durante a execução da Etapa 6."
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        except Exception as e:
            error_msg = f"Erro na Etapa 6: {str(e)}"
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        finally:
            self.finished_with_result.emit(result)
