import subprocess
import os
import math
import re
import time
from PyQt6.QtCore import QThread, pyqtSignal

class HardwareInspectionTask(QThread):
    """Thread assíncrona para Coleta de Hardware (Processador, RAM, Armazenamento C:) via WMI (Invoke-WmiMethod) com leitura via UNC e credenciais seguras."""
    output_ready = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)  # percent, status_text
    finished_with_result = pyqtSignal(dict)   # dicionário com resultados tratadas

    def __init__(self, target_host: str, admin_user: str = "", admin_password: str = "", parent=None):
        super().__init__(parent)
        self.target_host = target_host.strip()
        self.admin_user = admin_user.strip()
        self.admin_password = admin_password

    def _execute_wmi_cmd(self, cmd_content: str, temp_filename: str = "", timeout: int = 30) -> str:
        """Executa um comando remoto via WMI (Invoke-WmiMethod Win32_Process) sem expor senhas no CLI.
        Se temp_filename for fornecido, a saída do comando será redirecionada para C:\\Windows\\Temp\\temp_filename
        e lida via caminho UNC (\\\\target_host\\c$\\Windows\\Temp\\temp_filename)."""
        
        unc_path = f"\\\\{self.target_host}\\c$\\Windows\\Temp\\{temp_filename}" if temp_filename else ""
        remote_path = f"C:\\Windows\\Temp\\{temp_filename}" if temp_filename else ""

        # Garante que não haja arquivo residual antigo no destino UNC
        if unc_path and os.path.exists(unc_path):
            try:
                os.remove(unc_path)
            except Exception:
                pass

        cmd_to_run = f"{cmd_content} > {remote_path}" if temp_filename else cmd_content

        # Escapar aspas simples no comando CMD se existirem
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

        # Aguardar gravação do arquivo de saída via UNC
        start_time = time.time()
        max_wait = 12
        while time.time() - start_time < max_wait:
            if os.path.exists(unc_path) and os.path.getsize(unc_path) > 0:
                time.sleep(0.5)  # Pequena pausa para conclusão de escrita
                break
            time.sleep(0.5)

        if not os.path.exists(unc_path):
            return ""

        output_content = ""
        try:
            # Tenta decodificar com diferentes encodings comuns do Windows/CMD
            for enc in ['utf-16', 'utf-8', 'cp850', 'latin1']:
                try:
                    with open(unc_path, 'r', encoding=enc) as f:
                        output_content = f.read()
                    if output_content.strip():
                        break
                except Exception:
                    continue
        finally:
            # Deletar arquivo temporário via UNC
            try:
                if os.path.exists(unc_path):
                    os.remove(unc_path)
            except Exception:
                pass

        return output_content

    def run(self):
        self.output_ready.emit(f"Iniciando Coleta de Informações de Hardware em {self.target_host} via WMI...")
        self.progress_updated.emit(10, "Em Execução")

        result = {
            "success": False,
            "cpu_name": "Não identificado",
            "ram_gb": "Não identificado",
            "free_space_gb": "****",
            "total_space_gb": "****",
            "error": ""
        }

        try:
            # -------------------------------------------------------------
            # 1. PROCESSADOR (WMIC com fallback PowerShell via WMI)
            # -------------------------------------------------------------
            self.output_ready.emit("Executando consulta do Processador via WMI...")
            out_cpu = self._execute_wmi_cmd("wmic cpu get Name", temp_filename="hw_cpu.txt")
            cpu_name = self._parse_cpu_name(out_cpu)

            if cpu_name == "Não identificado":
                self.output_ready.emit("Tentando fallback de consulta do Processador via PowerShell...")
                out_cpu_ps = self._execute_wmi_cmd("powershell -NoProfile -Command \"(Get-CimInstance Win32_Processor).Name\"", temp_filename="hw_cpu.txt")
                cpu_name = self._parse_cpu_name(out_cpu_ps)

            result["cpu_name"] = cpu_name
            self.output_ready.emit(f"Processador identificado: {result['cpu_name']}")
            self.progress_updated.emit(35, "Em Execução")

            # -------------------------------------------------------------
            # 2. MEMÓRIA RAM (WMIC com fallback PowerShell via WMI)
            # -------------------------------------------------------------
            self.output_ready.emit("Executando consulta da Memória RAM via WMI...")
            out_ram = self._execute_wmi_cmd("wmic computersystem get TotalPhysicalMemory", temp_filename="hw_ram.txt")
            ram_gb = self._parse_ram_gb(out_ram)

            if ram_gb == "Não identificado":
                self.output_ready.emit("Tentando fallback de consulta da Memória RAM via PowerShell...")
                out_ram_ps = self._execute_wmi_cmd("powershell -NoProfile -Command \"(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory\"", temp_filename="hw_ram.txt")
                ram_gb = self._parse_ram_gb(out_ram_ps)

            result["ram_gb"] = ram_gb
            self.output_ready.emit(f"Memória RAM calculada: {result['ram_gb']}")
            self.progress_updated.emit(60, "Em Execução")

            # -------------------------------------------------------------
            # 3. ARMAZENAMENTO (WMIC com fallback PowerShell via WMI)
            # -------------------------------------------------------------
            self.output_ready.emit("Executando consulta do Armazenamento (Disco C:) via WMI...")
            out_disk = self._execute_wmi_cmd("wmic logicaldisk get Name,FreeSpace,Size", temp_filename="hw_disk.txt")
            free_gb, total_gb = self._parse_disk_info(out_disk)

            if free_gb == "****":
                self.output_ready.emit("Tentando fallback de consulta do Disco C: via PowerShell...")
                out_disk_ps = self._execute_wmi_cmd("powershell -NoProfile -Command \"Get-CimInstance Win32_LogicalDisk -Filter \\\"DeviceID='C:'\\\" | Select-Object DeviceID, FreeSpace, Size\"", temp_filename="hw_disk.txt")
                free_gb, total_gb = self._parse_disk_info(out_disk_ps)

            result["free_space_gb"] = free_gb
            result["total_space_gb"] = total_gb
            self.output_ready.emit(f"Disco C: -> Livre: {free_gb} GB | Total: {total_gb} GB")
            self.progress_updated.emit(85, "Em Execução")

            result["success"] = True
            self.progress_updated.emit(100, "Concluído")
            self.output_ready.emit("✅ Coleta de Hardware realizada com sucesso via WMI!")

        except TimeoutError as te:
            error_msg = str(te)
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        except Exception as e:
            error_msg = f"Erro na coleta de hardware: {str(e)}"
            result["error"] = error_msg
            result["success"] = False
            self.output_ready.emit(f"❌ {error_msg}")
            self.progress_updated.emit(0, "Erro")
        finally:
            self.finished_with_result.emit(result)

    def _parse_cpu_name(self, content: str) -> str:
        """Limpa cabeçalhos e obtém o nome do Processador."""
        if not content:
            return "Não identificado"
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            if "Name" in line or "Win32_Processor" in line:
                continue
            return line
        return "Não identificado"

    def _parse_ram_gb(self, content: str) -> str:
        """Converte Bytes para GB comercial (math.ceil)."""
        if not content:
            return "Não identificado"
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            if "TotalPhysicalMemory" in line:
                continue
            numbers = re.findall(r'\d+', line)
            if numbers:
                try:
                    bytes_val = int(numbers[0])
                    if bytes_val > 100000:
                        gb_val = math.ceil(bytes_val / (1024 ** 3))
                        return f"{gb_val} GB"
                except Exception:
                    pass
        return "Não identificado"

    def _parse_disk_info(self, content: str) -> tuple[str, str]:
        """Extrai FreeSpace e Size em GB com 2 casas decimais apenas para o Disco C:."""
        if not content:
            return "****", "****"
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            if "C:" in line.upper():
                tokens = line.split()
                numbers = [t for t in tokens if t.isdigit()]
                if len(numbers) >= 2:
                    val1 = int(numbers[0])
                    val2 = int(numbers[1])
                    free_bytes = min(val1, val2)
                    total_bytes = max(val1, val2)
                    
                    free_gb = free_bytes / (1024 ** 3)
                    total_gb = total_bytes / (1024 ** 3)
                    
                    return f"{free_gb:.2f}", f"{total_gb:.2f}"
        return "****", "****"

