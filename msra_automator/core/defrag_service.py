import subprocess
import os
import time
from PyQt6.QtCore import QThread, pyqtSignal

class DiskDefragTask(QThread):
    """Thread assíncrona para a Etapa 3: Identificação de mídia (HDD/SSD) e execução de defrag C: /O via WMI com credenciais seguras."""
    output_ready = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)             # percent, status_text
    media_type_detected = pyqtSignal(str, str)          # media_type ('HDD'/'SSD'), notice_message
    finished_with_result = pyqtSignal(dict)              # resultado final

    def __init__(self, target_host: str, admin_user: str = "", admin_password: str = "", parent=None):
        super().__init__(parent)
        self.target_host = target_host.strip()
        self.admin_user = admin_user.strip()
        self.admin_password = admin_password

    def _execute_wmi_cmd(self, cmd_content: str, temp_filename: str = "", timeout: int = 30) -> str:
        """Executa um comando remoto via WMI sem expor senhas no CLI."""
        unc_path = f"\\\\{self.target_host}\\c$\\Windows\\Temp\\{temp_filename}" if temp_filename else ""
        remote_path = f"C:\\Windows\\Temp\\{temp_filename}" if temp_filename else ""

        if unc_path and os.path.exists(unc_path):
            try:
                os.remove(unc_path)
            except Exception:
                pass

        cmd_to_run = f"{cmd_content} > {remote_path}" if temp_filename else cmd_content
        cmd_escaped = cmd_to_run.replace("'", "''")

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
        except subprocess.TimeoutExpired:
            raise TimeoutError("Tempo limite excedido ao disparar WMI via PowerShell.")

        if not temp_filename:
            return process.stdout or ""

        start_time = time.time()
        max_wait = 10
        while time.time() - start_time < max_wait:
            if os.path.exists(unc_path) and os.path.getsize(unc_path) > 0:
                time.sleep(0.5)
                break
            time.sleep(0.5)

        if not os.path.exists(unc_path):
            return ""

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
        finally:
            try:
                if os.path.exists(unc_path):
                    os.remove(unc_path)
            except Exception:
                pass

        return output_content

    def run(self):
        self.output_ready.emit(f"Iniciando Etapa 3: Desfragmentação e Otimização do Disco em {self.target_host} via WMI...")
        self.progress_updated.emit(10, "Em Execução")

        result = {
            "success": False,
            "media_type": "Desconhecido",
            "error": ""
        }

        try:
            # -------------------------------------------------------------
            # PASSO 1: IDENTIFICAR TIPO DE DISCO (HDD vs SSD) VIA POWERSHELL WMI
            # -------------------------------------------------------------
            self.output_ready.emit("Consultando tipo de mídia (HDD/SSD) via WMI...")
            out_media = self._execute_wmi_cmd("powershell -NoProfile -Command \"(Get-PhysicalDisk).MediaType\"", temp_filename="defrag_media.txt")

            media_type = "HDD"
            notice_msg = "Mídia de armazenamento detectada. Executando otimização do disco..."

            out_upper = (out_media or "").upper()
            if "SSD" in out_upper:
                media_type = "SSD"
                notice_msg = "SSD detectado. Executando otimização rápida (TRIM)..."
            elif "HDD" in out_upper:
                media_type = "HDD"
                notice_msg = "Disco Rígido (HDD) detectado. O processo pode levar vários minutos. Aguarde a conclusão..."

            result["media_type"] = media_type
            self.output_ready.emit(f"Mídia de armazenamento: {media_type}")
            self.media_type_detected.emit(media_type, notice_msg)
            self.progress_updated.emit(50, "Em Execução")

            # -------------------------------------------------------------
            # PASSO 2: EXECUÇÃO DA OTIMIZAÇÃO (defrag C: /O) VIA WMI
            # -------------------------------------------------------------
            self.output_ready.emit("Disparando comando 'defrag C: /O' via WMI...")
            self.output_ready.emit("Aguardando confirmação de disparo do processo de otimização de disco...")

            self._execute_wmi_cmd("defrag C: /O")

            self.output_ready.emit("✅ Comando de Otimização de disco enviado e iniciado com sucesso!")
            result["success"] = True
            self.progress_updated.emit(100, "Concluído")

        except TimeoutError as te:
            error_msg = str(te)
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        except Exception as e:
            error_msg = f"Erro na desfragmentação de disco: {str(e)}"
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        finally:
            self.finished_with_result.emit(result)

