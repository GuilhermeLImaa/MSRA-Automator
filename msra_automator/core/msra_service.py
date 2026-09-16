import time
import os
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError

class MSRAService:
    @staticmethod
    def connect_to_host(hostname: str):
        """
        Executa a automação para conectar ao MSRA sem uso de coordenadas,
        navegando pelas opções do menu até a inserção do destino.
        """
        try:
            # 1. Abrir msra.exe via ShellExecute para evitar Erro 740 e ocultar janela de comando
            os.startfile("msra.exe")
            time.sleep(1.5)  # Dá tempo para o processo ser registrado no SO
            
            # Conecta ao processo já aberto
            app = Application(backend="uia").connect(path=r"msra.exe", timeout=10)
            
            # 2. Aguardar janela principal
            main_window = app.window(title_re=".*Assistência Remota.*")
            main_window.wait('ready', timeout=15)
            
            # 3. Clicar em "Ajudar alguém que convidou você"
            help_someone_btn = main_window.child_window(title_re=".*Ajudar alguém.*", found_index=0)
            help_someone_btn.wait('visible', timeout=10)
            try:
                help_someone_btn.invoke()
            except Exception:
                help_someone_btn.click_input()
                
            time.sleep(1) # Aguarda a transição de tela do MSRA
            
            # 4. Clicar em "Opção de conexão avançada..."
            advanced_btn = main_window.child_window(title_re=".*conexão avançada.*", found_index=0)
            advanced_btn.wait('visible', timeout=10)
            try:
                advanced_btn.invoke()
            except Exception:
                advanced_btn.click_input()
                
            time.sleep(1) # Aguarda a transição de tela do MSRA
            
            # 5. Preencher hostname
            edit_box = main_window.child_window(control_type="Edit", found_index=0)
            edit_box.wait('visible', timeout=10)
            edit_box.set_edit_text(hostname)
            
            # 6. Clicar em Avançar
            try:
                next_btn = main_window.child_window(title="Avançar", control_type="Button")
                next_btn.invoke()
            except ElementNotFoundError:
                # Fallback caso o SO esteja em inglês
                try:
                    next_btn = main_window.child_window(title="Next", control_type="Button")
                    next_btn.invoke()
                except ElementNotFoundError:
                    main_window.type_keys("{ENTER}")
                    
            return True, f"Conexão iniciada com {hostname}"
            
        except Exception as e:
            return False, f"Erro na automação do MSRA: {str(e)}"
