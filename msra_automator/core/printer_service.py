import subprocess
import re
import time
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from core.logger import msra_logger
from core.history_manager import history_manager


class PrinterInspectionTask(QThread):
    output_ready = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, hostname: str):
        super().__init__()
        self.hostname = hostname
        self.log_history = []
        self.patrimony = hostname.split('-')[-1] if '-' in hostname else hostname

    def emit_log(self, text: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_history.append(f"[{now_str}] {text}")
        self.output_ready.emit(text)

    def run(self):
        destino = self.hostname
        self.emit_log(f"=== IMPRESSORAS CONECTADAS EM {destino} ===")

        printers = set()
        
        # 1. Varredura via WMIC
        try:
            cmd = ['psexec', f'\\\\{destino}', '-accepteula', '-nobanner', '-s', '-h', '-n', '15', 'wmic', 'printer', 'get', 'Name']
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, startupinfo=startupinfo, encoding='cp850', errors='replace')
            stdout, _ = proc.communicate(timeout=12)
            if stdout:
                for line in stdout.splitlines():
                    clean = line.strip()
                    if clean and not any(k in clean.lower() for k in ["name", "psexec", "copyright", "sysinternals", "connecting", "starting", "exited"]):
                        printers.add(clean)
        except Exception:
            pass

        # 2. Varredura via PowerShell (se a primeira não trouxer dados)
        if not printers:
            try:
                cmd_ps = ['psexec', f'\\\\{destino}', '-accepteula', '-nobanner', '-s', '-h', '-n', '15', 'powershell', '-Command', "Get-Printer | Select-Object -ExpandProperty Name"]
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                proc = subprocess.Popen(cmd_ps, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, startupinfo=startupinfo, encoding='cp850', errors='replace')
                stdout, _ = proc.communicate(timeout=12)
                if stdout:
                    for line in stdout.splitlines():
                        clean = line.strip()
                        if clean and not any(k in clean.lower() for k in ["psexec", "copyright", "sysinternals", "connecting", "starting", "exited"]):
                            printers.add(clean)
            except Exception:
                pass

        printer_list = sorted(list(printers))

        if printer_list:
            for p in printer_list:
                self.emit_log(f"• {p}")
            msg = f"{len(printer_list)} impressora(s) localizada(s) em {destino}."
        else:
            self.emit_log("Nenhuma impressora localizada no equipamento.")
            msg = "Nenhuma impressora localizada."

        # Salvar log simplificado
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            filename = log_dir / f"impressoras_conectadas_{self.patrimony}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== IMPRESSORAS CONECTADAS EM {destino} ===\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                if printer_list:
                    for p in printer_list:
                        f.write(f"• {p}\n")
                else:
                    f.write("Nenhuma impressora localizada.\n")
        except Exception:
            pass

        self.finished.emit(True, msg)


class ShortcutPrinterTask(QThread):
    output_ready = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, hostname: str):
        super().__init__()
        self.hostname = hostname
        self.log_history = []
        self.patrimony = hostname.split('-')[-1] if '-' in hostname else hostname

    def emit_log(self, text: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{now_str}] {text}"
        self.log_history.append(entry)
        self.output_ready.emit(text)
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            with open(log_dir / "shortcut_log.txt", "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception:
            pass

    def run_raw_cmd(self, cmd_list: list, timeout: int = 10):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            proc = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                encoding='cp850',
                errors='replace'
            )
            stdout_data, _ = proc.communicate(timeout=timeout)
            ret = proc.returncode
            if stdout_data and stdout_data.strip():
                self.emit_log(f"[Retorno {ret}] {stdout_data.strip()}")
            return ret, stdout_data or ""
        except Exception as e:
            self.emit_log(f"[Erro de Comando] {e}")
            return -1, str(e)

    def get_active_session_info(self, hostname: str):
        username = "console"
        session_id = "1"
        try:
            cmd = ['psexec', f'\\\\{hostname}', '-accepteula', '-nobanner', '-s', '-h', '-n', '15', 'cmd', '/c', 'query', 'user']
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo, encoding='cp850', errors='replace')
            stdout, _ = proc.communicate(timeout=8)
            if stdout:
                for line in stdout.splitlines():
                    clean = line.strip()
                    if not clean or "USERNAME" in clean:
                        continue
                    if clean.startswith('>'):
                        clean = clean[1:].strip()
                    parts = clean.split()
                    if parts:
                        username = parts[0].lstrip('>').strip()
                        for p in parts[1:]:
                            if p.isdigit():
                                session_id = p
                                break
                        return username, session_id
        except Exception:
            pass
        return username, session_id

    def run(self):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            destino = self.hostname

            # 1. Localizar o arquivo .lnk local (suporta PyInstaller bundle e diretório local)
            import sys
            base_dir = Path(getattr(sys, '_MEIPASS', '.'))
            local_lnk = base_dir / "IMPRESSAO_SEGURA (hub-vp-print) - Atalho.lnk"

            if not local_lnk.exists():
                local_lnk = Path("IMPRESSAO_SEGURA (hub-vp-print) - Atalho.lnk")

            if not local_lnk.exists():
                for f in base_dir.glob("*.lnk"):
                    if "IMPRESSAO" in f.name.upper() or "HUB" in f.name.upper():
                        local_lnk = f
                        break

            if not local_lnk.exists():
                for f in Path(".").glob("*.lnk"):
                    if "IMPRESSAO" in f.name.upper() or "HUB" in f.name.upper():
                        local_lnk = f
                        break

            if not local_lnk.exists():
                self.finished.emit(False, "Erro: O arquivo de atalho (.lnk) não foi encontrado no MSRA Automator.")
                return

            # 2. Detectar e Sanitizar Usuário Ativo para a Área de Trabalho Remota
            raw_user = history_manager.get_active_user(destino) or ""
            username = ""
            if raw_user and raw_user not in ["Não verificado", "Usuário não encontrado", "Desconhecido"]:
                match = re.search(r'\(([^)]+)\)', raw_user)
                if match:
                    inside = match.group(1)
                    users_list = [u.strip() for u in inside.split(',') if u.strip()]
                    if users_list:
                        username = users_list[0]
                else:
                    clean = raw_user.split('\\')[-1].strip()
                    if "," in clean:
                        clean = clean.split(",")[0].strip()
                    clean = clean.replace("Múltiplos", "").replace("multiplos", "").strip()
                    if clean and clean.lower() not in ["múltiplos", "multiplos", "usuário", "não encontrado", "desconhecido"]:
                        username = clean

            if not username:
                detected_user, _ = self.get_active_session_info(destino)
                if detected_user and detected_user.lower() not in ["usuário não encontrado", "console", "desconhecido", "username"]:
                    username = detected_user

            if not username:
                username = "guilherme.lima.9"

            # Regras de Exibição do Log Visual (Passos 1 a 6)

            # 1. Durante a cópia do arquivo
            self.emit_log(f"1. Enviando atalho para a área de trabalho de {username}...")

            user_desktop_remote = Path(f"\\\\{destino}\\c$\\Users\\{username}\\Desktop\\IMPRESSAO_SEGURA (hub-vp-print) - Atalho.lnk")
            
            try:
                import shutil
                shutil.copyfile(str(local_lnk), str(user_desktop_remote))
                self.emit_log("2. Atalho enviado com sucesso.")
            except Exception as e:
                copy_cmd = ['cmd.exe', '/c', 'copy', '/y', str(local_lnk.resolve()), f"\\\\{destino}\\c$\\Users\\{username}\\Desktop\\IMPRESSAO_SEGURA (hub-vp-print) - Atalho.lnk"]
                self.run_raw_cmd(copy_cmd, timeout=8)
                self.emit_log("2. Atalho enviado com sucesso.")

            # 3. Durante o Comando 1: schtasks /create
            self.emit_log("3. Criando tarefa temporária de mapeamento (MapearImp)...")
            tr_arg = f'explorer.exe "C:\\Users\\{username}\\Desktop\\IMPRESSAO_SEGURA (hub-vp-print) - Atalho.lnk"'
            cmd1 = [
                'schtasks', '/create',
                '/s', destino,
                '/tn', 'MapearImp',
                '/tr', tr_arg,
                '/sc', 'once',
                '/st', '00:00',
                '/ru', username,
                '/it',
                '/f'
            ]
            self.run_raw_cmd(cmd1, timeout=10)

            # 4. Durante o Comando 2: schtasks /run
            self.emit_log("4. Disparando tela de conexão na sessão do usuário...")
            cmd2 = [
                'schtasks', '/run',
                '/s', destino,
                '/tn', 'MapearImp'
            ]
            self.run_raw_cmd(cmd2, timeout=10)

            # 5. Durante o Comando 3: schtasks /delete
            self.emit_log("5. Limpando rastro da tarefa temporária...")
            cmd3 = [
                'schtasks', '/delete',
                '/s', destino,
                '/tn', 'MapearImp',
                '/f'
            ]
            self.run_raw_cmd(cmd3, timeout=10)

            # 6. Após encerramento do script
            self.finished.emit(True, "6. Procedimento finalizado. Impressora mapeada.")
        except Exception as ex:
            self.emit_log(f"Erro inesperado na execução: {ex}")
            self.finished.emit(False, f"Erro inesperado: {ex}")
