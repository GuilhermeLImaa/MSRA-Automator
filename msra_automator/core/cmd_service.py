import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class LocalCMDTask(QThread):
    """Executa um comando no Prompt de Comando (CMD) Administrador localmente."""
    output_ready = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, command_text: str):
        super().__init__()
        self.command_text = command_text

    def emit_log(self, text: str):
        self.output_ready.emit(text)

    def run(self):
        self.emit_log(f"--- EXECUTANDO COMANDO CMD ADMINISTRADOR LOCAL ---")
        self.emit_log(f"> {self.command_text}\n")

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            # Executa o comando via cmd.exe /c
            process = subprocess.Popen(
                ['cmd.exe', '/c', self.command_text],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                encoding='cp850',
                errors='replace'
            )

            for line in process.stdout:
                clean_line = line.rstrip('\r\n')
                if clean_line:
                    self.emit_log(clean_line)

            process.wait()

            if process.returncode == 0:
                self.finished.emit(True, "Comando executado com sucesso.")
            else:
                self.finished.emit(False, f"Comando finalizado com código de retorno: {process.returncode}")

        except Exception as e:
            self.emit_log(f"Erro ao executar comando: {str(e)}")
            self.finished.emit(False, f"Erro ao executar comando: {str(e)}")
