import subprocess
import os
import re
from PyQt6.QtCore import QThread, pyqtSignal

class TempCleanupTask(QThread):
    """Thread assíncrona para a Etapa 4: Limpeza silenciosa das pastas temporárias (Windows Temp, Prefetch e %temp% do usuário) via WMI com credenciais seguras."""
    output_ready = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)  # percent, status_text
    finished_with_result = pyqtSignal(dict)   # resultado final

    def __init__(self, target_host: str, active_user: str, admin_user: str = "", admin_password: str = "", parent=None):
        super().__init__(parent)
        self.target_host = target_host.strip()
        self.raw_user = active_user.strip()
        self.admin_user = admin_user.strip()
        self.admin_password = admin_password

    def _execute_wmi_cmd(self, cmd_content: str, temp_filename: str = "", timeout: int = 60) -> str:
        """Executa um comando remoto via WMI sem expor senhas no CLI.
        Se temp_filename for fornecido, a saída do comando será redirecionada para C:\\Windows\\Temp\\temp_filename
        e lida via caminho UNC (\\\\target_host\\c$\\Windows\\Temp\\temp_filename)."""
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

        import time
        start_time = time.time()
        max_wait = 10
        while time.time() - start_time < max_wait:
            if os.path.exists(unc_path) and os.path.getsize(unc_path) > 0:
                time.sleep(0.3)
                break
            time.sleep(0.4)

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
        self.output_ready.emit(f"Iniciando Etapa 4: Limpeza de Pastas Temporárias em {self.target_host} via WMI...")
        self.progress_updated.emit(10, "Em Execução")

        result = {
            "success": False,
            "error": ""
        }

        user_str = self.raw_user
        match = re.search(r'\(([^)]+)\)', user_str)
        if match:
            inside = match.group(1)
            users_list = [u.strip() for u in inside.split(',') if u.strip()]
            if users_list:
                user_str = users_list[0]

        clean_user = user_str.split('\\')[-1].strip()
        clean_user = clean_user.replace("Múltiplos", "").replace("multiplos", "").strip()

        try:
            deleted_files = 0
            # Contagem de arquivos temporários antes da remoção via UNC
            try:
                count_cmd = f"powershell -NoProfile -Command \"$c = 0; @('C:\\Windows\\Temp','C:\\Windows\\Prefetch', 'C:\\Users\\{clean_user}\\AppData\\Local\\Temp') | ForEach-Object {{ if (Test-Path $_) {{ $files = Get-ChildItem $_ -Recurse -File -ErrorAction SilentlyContinue; if ($files) {{ $c += $files.Count }} }} }}; Write-Output $c\""
                out_cnt = self._execute_wmi_cmd(count_cmd, temp_filename="temp_count.txt", timeout=20)
                if out_cnt:
                    nums = re.findall(r'\d+', out_cnt.strip())
                    if nums:
                        deleted_files = int(nums[0])
            except Exception:
                pass

            # -------------------------------------------------------------
            # 1. LIMPEZA DA PASTA WINDOWS TEMP
            # -------------------------------------------------------------
            self.output_ready.emit("Limpando pasta C:\\Windows\\Temp via WMI...")
            cmd_temp1 = 'del /q /f /s C:\\Windows\\Temp\\* & for /d %i in (C:\\Windows\\Temp\\*) do rmdir /q /s "%i"'
            self._execute_wmi_cmd(cmd_temp1)

            self.progress_updated.emit(40, "Em Execução")
            self.output_ready.emit("✅ Limpeza da pasta C:\\Windows\\Temp efetuada.")

            # -------------------------------------------------------------
            # 2. LIMPEZA DA PASTA WINDOWS PREFETCH
            # -------------------------------------------------------------
            self.output_ready.emit("Limpando pasta C:\\Windows\\Prefetch via WMI...")
            cmd_temp2 = 'del /q /f /s C:\\Windows\\Prefetch\\* & for /d %i in (C:\\Windows\\Prefetch\\*) do rmdir /q /s "%i"'
            self._execute_wmi_cmd(cmd_temp2)

            self.progress_updated.emit(70, "Em Execução")
            self.output_ready.emit("✅ Limpeza da pasta C:\\Windows\\Prefetch efetuada.")

            # -------------------------------------------------------------
            # 3. LIMPEZA DA PASTA %TEMP% DO USUÁRIO ATIVO
            # -------------------------------------------------------------
            if clean_user and clean_user != "Desconhecido":
                self.output_ready.emit(f"Limpando pasta %temp% do usuário '{clean_user}' via WMI...")
                cmd_temp3 = f'del /q /f /s C:\\Users\\{clean_user}\\AppData\\Local\\Temp\\* & for /d %i in (C:\\Users\\{clean_user}\\AppData\\Local\\Temp\\*) do rmdir /q /s "%i"'
                self._execute_wmi_cmd(cmd_temp3)
                self.output_ready.emit(f"✅ Limpeza da pasta %temp% do usuário '{clean_user}' efetuada.")
            else:
                self.output_ready.emit("⚠️ Usuário ativo não especificado. Pulando limpeza de %temp% do usuário.")

            result["success"] = True
            result["deleted_files_count"] = deleted_files
            self.progress_updated.emit(100, "Concluído")
            
            if deleted_files > 0:
                fmt_count = f"{deleted_files:,}".replace(",", ".")
                self.output_ready.emit(f"✨ Limpeza concluída! Total de {fmt_count} arquivos apagados.")
            else:
                self.output_ready.emit("✨ Limpeza de pastas temporárias concluída com sucesso!")

        except TimeoutError as te:
            error_msg = str(te)
            result["success"] = False
            result["error"] = error_msg
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        except Exception as e:
            error_msg = f"Erro na limpeza de temporários: {str(e)}"
            result["success"] = False
            result["error"] = error_msg
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        finally:
            self.finished_with_result.emit(result)

