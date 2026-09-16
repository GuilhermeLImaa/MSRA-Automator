import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ActiveUserTask(QThread):
    """Consulta de forma assíncrona o usuário ativo em um computador remoto usando query user nativo."""
    finished = pyqtSignal(str, str) # Emite (hostname, user_str)

    def __init__(self, hostname: str):
        super().__init__()
        self.hostname = hostname

    def parse_query_user_output(self, stdout_text: str) -> list[str]:
        found_users = []
        if not stdout_text:
            return found_users

        for line in stdout_text.splitlines():
            clean = line.strip()
            if not clean:
                continue
            # Ignora cabeçalhos do query user
            if any(k in clean for k in ["USERNAME", "NOME DO USU", "SESSIONNAME", "Copyright", "PsExec"]):
                continue
            
            # Remove indicador '>' de sessão ativa
            if clean.startswith('>'):
                clean = clean[1:].strip()
                
            parts = clean.split()
            if parts:
                candidate = parts[0].lstrip('>').strip()
                if candidate and candidate.lower() not in ["username", "usuario", "usuário", "nome"]:
                    if '\\' in candidate:
                        candidate = candidate.split('\\')[-1]
                    if candidate not in found_users:
                        found_users.append(candidate)
                        
        return found_users

    def run(self):
        found_users = []
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # 1. Executa query user /server:HOSTNAME nativo
        try:
            cmd = ['cmd.exe', '/c', 'query', 'user', f'/server:{self.hostname}']
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                encoding='cp850',
                errors='replace'
            )
            stdout_data, _ = proc.communicate(timeout=6)
            if stdout_data:
                found_users = self.parse_query_user_output(stdout_data)
        except Exception:
            pass

        # 2. Fallback: quser /server:HOSTNAME
        if not found_users:
            try:
                cmd = ['cmd.exe', '/c', 'quser', f'/server:{self.hostname}']
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo,
                    encoding='cp850',
                    errors='replace'
                )
                stdout_data, _ = proc.communicate(timeout=6)
                if stdout_data:
                    found_users = self.parse_query_user_output(stdout_data)
            except Exception:
                pass

        # Formatação do resultado
        if len(found_users) == 1:
            result_str = found_users[0]
        elif len(found_users) > 1:
            users_list_str = ", ".join(found_users)
            result_str = f"Múltiplos usuários ativos ({users_list_str})"
        else:
            result_str = "Usuário não encontrado"

        self.finished.emit(self.hostname, result_str)

