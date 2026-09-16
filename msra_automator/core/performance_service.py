import subprocess
import os
import re
import time
from PyQt6.QtCore import QThread, pyqtSignal

class PerformanceAdjustmentTask(QThread):
    """Thread assíncrona para a Etapa 2: Captura do SID via Win32_UserProfile e injeção de chaves de registro para Melhor Desempenho via WMI."""
    output_ready = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)  # percent, status_text
    finished_with_result = pyqtSignal(dict)   # dicionário com resultado

    def __init__(self, target_host: str, active_user: str, admin_user: str = "", admin_password: str = "", parent=None):
        super().__init__(parent)
        self.target_host = target_host.strip()
        self.raw_user = active_user.strip()
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
        max_wait = 12
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
        self.output_ready.emit(f"Iniciando Ajuste das Configurações de Desempenho em {self.target_host} via WMI...")
        self.progress_updated.emit(10, "Em Execução")

        result = {
            "success": False,
            "sid": "",
            "error": ""
        }

        # Tratamento do nome de usuário (remover domínio ou extrair de "Múltiplos usuários ativos (user1, user2)")
        user_str = self.raw_user
        match = re.search(r'\(([^)]+)\)', user_str)
        if match:
            inside = match.group(1)
            users_list = [u.strip() for u in inside.split(',') if u.strip()]
            if users_list:
                user_str = users_list[0]

        clean_user = user_str.split('\\')[-1].strip()
        clean_user = clean_user.replace("Múltiplos", "").replace("multiplos", "").strip()

        if not clean_user or clean_user == "Desconhecido":
            error_msg = f"Usuário ativo inválido ou não identificado: '{self.raw_user}'."
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
            result["error"] = error_msg
            self.finished_with_result.emit(result)
            return

        try:
            # -------------------------------------------------------------
            # PASSO 1: CAPTURA DINÂMICA DO SID VIA WIN32_USERPROFILE
            # -------------------------------------------------------------
            self.output_ready.emit(f"Capturando SID para o usuário '{clean_user}' via Win32_UserProfile...")
            cmd_sid = f"powershell.exe -NoProfile -Command \"Get-WmiObject Win32_UserProfile | Where-Object {{ $_.LocalPath -match '{clean_user}$' }} | Select-Object -ExpandProperty SID\""
            out_sid = self._execute_wmi_cmd(cmd_sid, temp_filename="perf_sid.txt")
            sid_str = self._parse_sid(out_sid)

            if not sid_str:
                self.output_ready.emit("Tentando fallback de consulta de perfil via Get-CimInstance...")
                cmd_sid_cim = f"powershell.exe -NoProfile -Command \"Get-CimInstance Win32_UserProfile | Where-Object {{ $_.LocalPath -match '{clean_user}$' }} | Select-Object -ExpandProperty SID\""
                out_sid_cim = self._execute_wmi_cmd(cmd_sid_cim, temp_filename="perf_sid.txt")
                sid_str = self._parse_sid(out_sid_cim)

            if not sid_str:
                self.output_ready.emit("Tentando fallback de consulta via Win32_UserAccount...")
                out_sid_ua = self._execute_wmi_cmd(f"wmic useraccount where name='{clean_user}' get sid", temp_filename="perf_sid.txt")
                sid_str = self._parse_sid(out_sid_ua)

            if not sid_str:
                raise Exception(f"Não foi possível identificar o SID para o usuário '{clean_user}' via Win32_UserProfile.")

            result["sid"] = sid_str
            self.output_ready.emit(f"✅ SID identificado com sucesso: {sid_str}")
            self.progress_updated.emit(50, "Em Execução")

            # -------------------------------------------------------------
            # PASSO 2: INJEÇÃO DAS CHAVES DE REGISTRO (MELHOR DESEMPENHO)
            # -------------------------------------------------------------
            self.output_ready.emit("Aplicando chave VisualFXSetting (DWORD 2) via WMI...")
            cmd_reg1 = f"reg add HKEY_USERS\\{sid_str}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects /v VisualFXSetting /t REG_DWORD /d 2 /f"
            self._execute_wmi_cmd(cmd_reg1)

            self.output_ready.emit("Aplicando chave UserPreferencesMask (REG_BINARY) via WMI...")
            cmd_reg2 = f"reg add \"HKEY_USERS\\{sid_str}\\Control Panel\\Desktop\" /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f"
            self._execute_wmi_cmd(cmd_reg2)

            self.output_ready.emit("Aplicando chave MinAnimate (REG_SZ 0) via WMI...")
            cmd_reg3 = f"reg add \"HKEY_USERS\\{sid_str}\\Control Panel\\Desktop\\WindowMetrics\" /v MinAnimate /t REG_SZ /d 0 /f"
            self._execute_wmi_cmd(cmd_reg3)

            result["success"] = True
            self.progress_updated.emit(100, "Concluído")
            self.output_ready.emit("✅ Ajuste de Desempenho Visual aplicado com sucesso!")
            self.output_ready.emit("ℹ️ Requer logoff do usuário para refletir totalmente na interface gráfica.")

        except TimeoutError as te:
            error_msg = str(te)
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ Erro ao ajustar desempenho: {error_msg}")
            self.progress_updated.emit(0, "Erro")
        finally:
            self.finished_with_result.emit(result)

    def _parse_sid(self, content: str) -> str:
        """Extrai o código de SID (S-1-5-...) do conteúdo lido."""
        if not content:
            return ""
        match = re.search(r'(S-1-5-[0-9\-]+)', content)
        if match:
            return match.group(1).strip()
        match_generic = re.search(r'(S-1-[0-9\-]+)', content)
        if match_generic:
            return match_generic.group(1).strip()
        return ""



