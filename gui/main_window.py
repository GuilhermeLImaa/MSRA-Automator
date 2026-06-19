from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QButtonGroup, QMessageBox,
    QApplication, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import subprocess
import re
from gui.styles import MAIN_STYLE
from gui.widgets import CardWidget
from models.hostname_builder import HostnameBuilder
from core.msra_service import MSRAService
from core.logger import msra_logger

class PingTask(QThread):
    output_ready = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, hostname):
        super().__init__()
        self.hostname = hostname

    def run(self):
        self.output_ready.emit(f"Pinging {self.hostname}...")
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        success = False
        ip_address = ""
        
        ip_pattern = re.compile(r"(?:Resposta de|Reply from)\s+([0-9a-fA-F\.\:]+)")
        brackets_pattern = re.compile(r"\[([0-9a-fA-F\.\:]+)\]")
        
        try:
            # -n 3 faz o ping 3 vezes
            process = subprocess.Popen(
                ['ping', '-n', '3', self.hostname],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                encoding='cp850'
            )
            
            for line in process.stdout:
                if line.strip():
                    linha = line.strip()
                    # Verifica se houve resposta com sucesso (Português ou Inglês)
                    if "Resposta de" in linha or "Reply from" in linha:
                        # Se contiver 'inacessível', 'falha', 'unreachable', 'failed', não conta como sucesso
                        if not any(x in linha.lower() for x in ["inacess", "unreach", "falha", "fail"]):
                            success = True
                            match = ip_pattern.search(linha)
                            if match:
                                ip_address = match.group(1).rstrip(':')
                    else:
                        if not ip_address:
                            match = brackets_pattern.search(linha)
                            if match:
                                ip_address = match.group(1).rstrip(':')
                    self.output_ready.emit(linha)
            
            process.wait()
        except Exception as e:
            self.output_ready.emit(f"Erro ao executar ping: {str(e)}")
            
        self.finished.emit(success, ip_address)

class MSRATask(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, hostname):
        super().__init__()
        self.hostname = hostname

    def run(self):
        success, message = MSRAService.connect_to_host(self.hostname)
        self.finished.emit(success, message)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Automação MSRA - Assistência Remota")
        self.resize(600, 650)
        self.setStyleSheet(MAIN_STYLE)
        
        self.selected_prefix = ""
        self.last_ping_ip = ""
        self.setup_ui()
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Splitter principal
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Widget superior
        self.top_widget = QWidget()
        top_layout = QVBoxLayout(self.top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)

        # Título
        title = QLabel("AUTOMAÇÃO ASSISTÊNCIA REMOTA")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(title)

        # Três cartões selecionáveis
        type_label = QLabel("Selecione o Tipo de Equipamento:")
        top_layout.addWidget(type_label)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        
        self.btn_wk = CardWidget("🖥 Computador\n(HUB-WK)", "HUB-WK")
        self.btn_md = CardWidget("🏥 Equip. Médico\n(HUB-MD)", "HUB-MD")
        self.btn_nt = CardWidget("💻 Notebook\n(HUB-NT)", "HUB-NT")

        self.btn_group.addButton(self.btn_wk, 1)
        self.btn_group.addButton(self.btn_md, 2)
        self.btn_group.addButton(self.btn_nt, 3)

        self.btn_group.buttonClicked.connect(self.on_type_selected)

        cards_layout.addWidget(self.btn_wk)
        cards_layout.addWidget(self.btn_md)
        cards_layout.addWidget(self.btn_nt)

        top_layout.addLayout(cards_layout)

        # Campo Patrimônio
        patrimony_label = QLabel("Número do Patrimônio:")
        top_layout.addWidget(patrimony_label)

        patrimony_layout = QHBoxLayout()
        self.patrimony_input = QLineEdit()
        self.patrimony_input.setPlaceholderText("Ex: 123456")
        self.patrimony_input.textChanged.connect(self.update_hostname)
        patrimony_layout.addWidget(self.patrimony_input)

        self.copy_hostname_button = QPushButton("📋")
        self.copy_hostname_button.setToolTip("Copiar Hostname completo")
        self.copy_hostname_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
                font-size: 16px;
                max-width: 36px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #888888;
                border: 1px solid #444444;
            }
        """)
        self.copy_hostname_button.setEnabled(False)
        self.copy_hostname_button.clicked.connect(self.copy_hostname_to_clipboard)
        patrimony_layout.addWidget(self.copy_hostname_button)
        
        top_layout.addLayout(patrimony_layout)

        # Botão Verificar
        self.verify_button = QPushButton("Verificar")
        self.verify_button.setObjectName("VerifyButton")
        self.verify_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #888888;
            }
        """)
        self.verify_button.setEnabled(False)
        self.verify_button.clicked.connect(self.on_verify_clicked)
        top_layout.addWidget(self.verify_button)

        # Campo Destino Gerado
        self.hostname_display = QLabel("Destino Gerado: ")
        self.hostname_display.setTextFormat(Qt.TextFormat.RichText)
        self.hostname_display.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #207bc1; 
            background-color: #3a3a3a;
            border: 1px solid #4d4d4d;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
        """)
        self.hostname_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.hostname_display)

        # Botão Executar
        self.action_button = QPushButton("Executar Conexão")
        self.action_button.setObjectName("ActionButton")
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self.on_execute_clicked)
        top_layout.addWidget(self.action_button)

        # Widget inferior
        self.bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(0, 10, 0, 0)
        bottom_layout.setSpacing(10)

        # Área de Status
        status_label = QLabel("Status do Ping / Conexão:")
        bottom_layout.addWidget(status_label)
        
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setPlaceholderText("Aguardando ação...")
        self.log_panel.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_panel.setFixedHeight(80)
        self.log_panel.textChanged.connect(self.adjust_log_panel_height)
        bottom_layout.addWidget(self.log_panel)

        self.copy_buttons_layout = QHBoxLayout()
        
        self.copy_ip_button = QPushButton("📋 Copiar IP")
        self.copy_ip_button.setObjectName("CopyIPButton")
        self.copy_ip_button.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #e0e0e0;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #444444;
                border: 1px solid #555555;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #242424;
                color: #555555;
                border: 1px solid #2d2d2d;
            }
        """)
        self.copy_ip_button.setEnabled(False)
        self.copy_ip_button.clicked.connect(self.copy_ip_to_clipboard)
        
        self.copy_log_button = QPushButton("📋 Copiar Relatório Completo")
        self.copy_log_button.setObjectName("CopyLogButton")
        self.copy_log_button.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #e0e0e0;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #444444;
                border: 1px solid #555555;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #242424;
                color: #555555;
                border: 1px solid #2d2d2d;
            }
        """)
        self.copy_log_button.setEnabled(False)
        self.copy_log_button.clicked.connect(self.copy_log_to_clipboard)
        
        self.copy_buttons_layout.addWidget(self.copy_ip_button)
        self.copy_buttons_layout.addWidget(self.copy_log_button)
        bottom_layout.addLayout(self.copy_buttons_layout)

        # Adiciona widgets ao splitter
        self.splitter.addWidget(self.top_widget)
        self.splitter.addWidget(self.bottom_widget)
        
        # Define os fatores de esticamento do splitter
        self.splitter.setStretchFactor(0, 0) # Topo não estica
        self.splitter.setStretchFactor(1, 1) # Status (baixo) estica
        
        main_layout.addWidget(self.splitter)



    def on_type_selected(self, button):
        self.selected_prefix = button.prefix_value
        self.update_hostname()

    def update_hostname(self):
        patrimony = self.patrimony_input.text()
        self.copy_ip_button.setEnabled(False)
        self.copy_log_button.setEnabled(False)
        self.last_ping_ip = ""
        
        if self.selected_prefix and patrimony:
            hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
            self.hostname_display.setText(f"Destino Pronto para Conexão:<br>{hostname}")
            self.action_button.setEnabled(True)
            self.verify_button.setEnabled(True)
            self.copy_hostname_button.setEnabled(True)
        else:
            self.hostname_display.setText("Destino Gerado: ")
            self.action_button.setEnabled(False)
            self.verify_button.setEnabled(False)
            self.copy_hostname_button.setEnabled(False)

    def append_status(self, text: str):
        self.log_panel.append(f"> {text}")
        scrollbar = self.log_panel.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_verify_clicked(self):
        patrimony = self.patrimony_input.text()
        if not self.selected_prefix or not patrimony.strip():
            return
            
        hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
        self.verify_button.setEnabled(False)
        self.action_button.setEnabled(False)
        self.copy_ip_button.setEnabled(False)
        self.copy_log_button.setEnabled(False)
        self.last_ping_ip = ""
        
        self.log_panel.clear()
        
        self.ping_thread = PingTask(hostname)
        self.ping_thread.output_ready.connect(self.append_status)
        self.ping_thread.finished.connect(self.on_ping_finished)
        self.ping_thread.start()

    def on_ping_finished(self, success, ip_address):
        self.verify_button.setEnabled(True)
        self.action_button.setEnabled(True)
        self.last_ping_ip = ip_address
        
        patrimony = self.patrimony_input.text()
        hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
        
        if success:
            status_html = "<span style='color: #4CAF50;'>🟢 Ativo</span>"
            self.copy_ip_button.setEnabled(bool(ip_address))
            self.copy_log_button.setEnabled(True)
        else:
            status_html = "<span style='color: #F44336;'>🔴 Inativo</span>"
            self.copy_ip_button.setEnabled(False)
            self.copy_log_button.setEnabled(False)
            
        self.hostname_display.setText(f"Destino Pronto para Conexão:<br>{hostname} &nbsp; {status_html}")

    def on_execute_clicked(self):
        patrimony = self.patrimony_input.text()
        
        if not self.selected_prefix:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um tipo de equipamento.")
            return
            
        if not patrimony.strip():
            QMessageBox.warning(self, "Aviso", "Por favor, insira o número do patrimônio.")
            return

        hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
        
        # Executa direto
        self.append_status(f"Iniciando automação para {hostname}...")
        self.action_button.setEnabled(False)
        self.verify_button.setEnabled(False)
        
        # Chamar automação (via QThread para não travar a tela)
        self.msra_thread = MSRATask(hostname)
        self.msra_thread.finished.connect(self.on_automation_finished)
        self.msra_thread.start()

    def on_automation_finished(self, success, message):
        self.append_status(message)
        self.action_button.setEnabled(True)
        self.verify_button.setEnabled(True)
        
        # Gravar log
        patrimony = self.patrimony_input.text()
        hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
        msra_logger.log_execution(self.selected_prefix, patrimony, hostname, message)

    def copy_to_clipboard(self, text):
        if not text:
            return False
        
        # 1. Tenta usar o clipboard do QApplication
        pyqt_ok = False
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            pyqt_ok = True
        except Exception as e:
            msra_logger.error(f"Erro ao copiar via PyQt: {e}")

        # 2. Tenta usar clip.exe como fallback ou para garantir que funciona em ambientes UAC elevados
        clip_ok = False
        try:
            # clip.exe está presente em todos os Windows modernos
            p = subprocess.Popen('clip', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            p.communicate(input=text)
            clip_ok = True
        except Exception as e:
            msra_logger.error(f"Erro ao copiar via clip.exe: {e}")
            
        return pyqt_ok or clip_ok

    def copy_hostname_to_clipboard(self):
        patrimony = self.patrimony_input.text()
        if self.selected_prefix and patrimony:
            hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
            if self.copy_to_clipboard(hostname):
                self.statusBar().showMessage(f"Hostname copiado: {hostname}", 3000)
            else:
                self.statusBar().showMessage("Falha ao copiar o hostname.", 3000)

    def copy_ip_to_clipboard(self):
        if self.last_ping_ip:
            if self.copy_to_clipboard(self.last_ping_ip):
                self.statusBar().showMessage(f"IP copiado: {self.last_ping_ip}", 3000)
            else:
                self.statusBar().showMessage("Falha ao copiar o IP.", 3000)
        else:
            self.statusBar().showMessage("Nenhum IP disponível para cópia.", 3000)

    def copy_log_to_clipboard(self):
        text = self.log_panel.toPlainText()
        lines = [line[2:] if line.startswith("> ") else line for line in text.split('\n')]
        cleaned_text = '\n'.join(lines)
        if self.copy_to_clipboard(cleaned_text.strip()):
            self.statusBar().showMessage("Relatório completo do ping copiado!", 3000)
        else:
            self.statusBar().showMessage("Falha ao copiar o relatório do ping.", 3000)

    def adjust_log_panel_height(self):
        doc_height = self.log_panel.document().size().height()
        # Adiciona um pequeno padding (margem) para evitar rolagem
        new_height = int(doc_height) + 15
        # Mantém limites de altura apropriados: mínimo de 80 e máximo de 300
        new_height = max(80, min(new_height, 300))
        self.log_panel.setFixedHeight(new_height)
