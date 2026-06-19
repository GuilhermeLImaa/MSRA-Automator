import time
from PyQt6.QtCore import QThread, pyqtSignal
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError
from core.logger import logger

class MSRAController(QThread):
    status_update = pyqtSignal(str)
    finished_execution = pyqtSignal(bool, str)

    def __init__(self, hostname: str):
        super().__init__()
        self.hostname = hostname

    def run(self):
        try:
            self.status_update.emit("Iniciando MSRA...")
            logger.info(f"Iniciando MSRA para o hostname: {self.hostname}")
            
            # Usando backend UIA (UI Automation)
            app = Application(backend="uia").start(r"msra.exe /offerra")
            self.status_update.emit("Aguardando janela do MSRA...")
            
            # Aguarda a janela principal (O título exato pode variar por versão do Windows, 
            # geralmente é 'Assistência Remota do Windows')
            main_window = app.window(title_re=".*Assistência Remota.*")
            main_window.wait('ready', timeout=15)
            
            self.status_update.emit("Digitando hostname...")
            
            # Localizar o campo de texto para o nome do computador
            # Em inglês é 'Type a computer name or IP address:' ou similar.
            # No Windows BR, é algo como 'Digitar um nome de computador ou endereço IP'
            # Usaremos o control_type Edit que geralmente é único nessa tela
            edit_box = main_window.child_window(control_type="Edit")
            edit_box.wait('visible', timeout=5)
            edit_box.set_edit_text(self.hostname)
            
            self.status_update.emit("Avançando...")
            time.sleep(0.5) # Pequena pausa para garantir a UI processar o texto
            
            # Localizar e clicar no botão Avançar / Next
            # Geralmente o nome é 'Avançar', mas podemos buscar por control_type='Button' e tentar pelo índice se o nome falhar
            try:
                next_button = main_window.child_window(title="Avançar", control_type="Button")
                next_button.click_input()
            except ElementNotFoundError:
                try:
                    next_button = main_window.child_window(title="Next", control_type="Button")
                    next_button.click_input()
                except ElementNotFoundError:
                    # Alternativa: tentar pegar o botão padrão
                    main_window.type_keys("{ENTER}")

            self.status_update.emit("Conexão iniciada!")
            logger.info("Processo de automação do MSRA concluído com sucesso.")
            self.finished_execution.emit(True, "Processo concluído.")

        except Exception as e:
            error_msg = f"Erro na automação: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.finished_execution.emit(False, error_msg)
