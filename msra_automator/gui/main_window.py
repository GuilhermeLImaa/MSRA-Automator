from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QButtonGroup, QMessageBox,
    QApplication, QSplitter, QFrame, QCompleter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QStringListModel
from PyQt6.QtGui import QTextCursor
import subprocess
import re
from gui.styles import MAIN_STYLE, SEGMENTED_BUTTON_STYLE
from gui.widgets import CardWidget
from models.hostname_builder import HostnameBuilder
from core.msra_service import MSRAService
from core.printer_service import PrinterInspectionTask, ShortcutPrinterTask
from core.logger import msra_logger
from core.history_manager import history_manager
from core.cmd_service import LocalCMDTask
from core.user_service import ActiveUserTask
from gui.history_dialog import HistoryDialog
from gui.optimization_dialog import OptimizationDialog
from utils.helpers import copy_to_clipboard as helper_copy_to_clipboard

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
            process = subprocess.Popen(
                ['ping', '-4', '-n', '3', self.hostname],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                encoding='cp850'
            )
            
            for line in process.stdout:
                if line.strip():
                    linha = line.strip()
                    if "Resposta de" in linha or "Reply from" in linha:
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
        self.setWindowTitle("Automação MSRA - Assistência Remota v2.0.0")
        self.resize(660, 840)
        self.setMinimumSize(640, 780)
        self.setStyleSheet(MAIN_STYLE)
        
        self.selected_prefix = ""
        self.last_ping_ip = ""
        self.pending_open_opt_dialog = False
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
        top_layout.setSpacing(10)

        # Título
        title = QLabel("AUTOMAÇÃO ASSISTÊNCIA REMOTA")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(title)

        # Três cartões selecionáveis
        self.type_label = QLabel("Selecione o Tipo de Equipamento:")
        top_layout.addWidget(self.type_label)

        self.cards_widget = QWidget()
        cards_layout = QHBoxLayout(self.cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(15)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        
        self.btn_wk = CardWidget("🖥 Computador\n(HUB-WK)", "HUB-WK")
        self.btn_md = CardWidget("🏥 Equip. Médico\n(HUB-MD)", "HUB-MD")
        self.btn_nt = CardWidget("💻 Notebook\n(HUB-NT)", "HUB-NT")

        self.btn_group.addButton(self.btn_wk, 1)
        self.btn_group.addButton(self.btn_md, 2)
        self.btn_group.addButton(self.btn_nt, 3)

        self.btn_wk.setChecked(True)
        self.selected_prefix = "HUB-WK"

        self.btn_group.buttonClicked.connect(self.on_type_selected)

        cards_layout.addWidget(self.btn_wk)
        cards_layout.addWidget(self.btn_md)
        cards_layout.addWidget(self.btn_nt)

        top_layout.addWidget(self.cards_widget)

        # Seletor de Tipo de Execução (Segmented Button Design)
        exec_title = QLabel("Tipo de Execução")
        exec_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 5px;")
        top_layout.addWidget(exec_title)

        exec_layout = QHBoxLayout()
        exec_layout.setSpacing(10)
        
        type_label = QLabel("Tipo:")
        type_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #e0e0e0;")
        exec_layout.addWidget(type_label)

        # Contêiner de Botões Segmentados
        self.segmented_container = QFrame()
        self.segmented_container.setObjectName("SegmentedContainer")
        self.segmented_container.setStyleSheet(SEGMENTED_BUTTON_STYLE)
        
        segmented_layout = QHBoxLayout(self.segmented_container)
        segmented_layout.setContentsMargins(3, 3, 3, 3)
        segmented_layout.setSpacing(2)

        self.action_type_group = QButtonGroup(self)
        self.action_type_group.setExclusive(True)

        self.btn_action_msra = QPushButton("Acesso Remoto (MSRA)")
        self.btn_action_msra.setObjectName("SegmentButton")
        self.btn_action_msra.setCheckable(True)
        self.btn_action_msra.setChecked(True)

        self.btn_action_printer = QPushButton("Conectar Impressão Segura")
        self.btn_action_printer.setObjectName("SegmentButton")
        self.btn_action_printer.setCheckable(True)

        self.btn_action_opt = QPushButton("Otimização")
        self.btn_action_opt.setObjectName("SegmentButton")
        self.btn_action_opt.setCheckable(True)

        self.action_type_group.addButton(self.btn_action_msra, 1)
        self.action_type_group.addButton(self.btn_action_printer, 2)
        self.action_type_group.addButton(self.btn_action_opt, 3)

        segmented_layout.addWidget(self.btn_action_msra, 1)
        segmented_layout.addWidget(self.btn_action_printer, 1)
        segmented_layout.addWidget(self.btn_action_opt, 1)

        exec_layout.addWidget(self.segmented_container, 1)
        top_layout.addLayout(exec_layout)

        # Botão de Diagnóstico de Impressoras Conectadas
        self.printer_path_container = QWidget()
        printer_path_layout = QVBoxLayout(self.printer_path_container)
        printer_path_layout.setContentsMargins(0, 5, 0, 5)
        printer_path_layout.setSpacing(5)

        self.inspect_button = QPushButton("🔍 Diagnóstico: Identificar Impressoras Conectadas")
        self.inspect_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: #ffffff;
                border: 1px solid #388e3c;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QPushButton:disabled {
                background-color: #1b5e20;
                color: #888888;
            }
        """)
        self.inspect_button.setEnabled(False)
        self.inspect_button.clicked.connect(self.on_inspect_clicked)
        printer_path_layout.addWidget(self.inspect_button)

        top_layout.addWidget(self.printer_path_container)
        self.printer_path_container.setVisible(False)

        self.action_type_group.buttonClicked.connect(self.on_action_type_changed)

        # Contêiner do Patrimônio
        self.patrimony_container = QWidget()
        patrimony_container_layout = QVBoxLayout(self.patrimony_container)
        patrimony_container_layout.setContentsMargins(0, 0, 0, 0)
        patrimony_container_layout.setSpacing(5)

        patrimony_label = QLabel("Número do Patrimônio:")
        patrimony_container_layout.addWidget(patrimony_label)

        patrimony_layout = QHBoxLayout()
        self.patrimony_input = QLineEdit()
        self.patrimony_input.setPlaceholderText("Ex: 123456")
        self.patrimony_input.textChanged.connect(self.update_hostname)
        
        # Configuração do Autocompletar (QCompleter)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        popup = self.completer.popup()
        popup.setStyleSheet("""
            QAbstractItemView {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #4d4d4d;
                selection-background-color: #207bc1;
                selection-color: #ffffff;
                font-size: 14px;
                padding: 4px;
            }
        """)
        self.patrimony_input.setCompleter(self.completer)
        self.update_completer()

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
        
        patrimony_container_layout.addLayout(patrimony_layout)

        # Botão Histórico de Acessos com Ícone de Relógio (entre o campo de patrimônio e verificar status)
        self.history_button = QPushButton("🕒 Histórico de Acessos")
        self.history_button.setToolTip("Abrir aba de histórico, favoritos e alertas")
        self.history_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: #207bc1;
                border: 1px solid #207bc1;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1a5c8e;
                color: #ffffff;
            }
        """)
        self.history_button.clicked.connect(self.open_history_dialog)
        patrimony_container_layout.addWidget(self.history_button)

        top_layout.addWidget(self.patrimony_container)

        # Botão Verificar
        self.verify_button = QPushButton("Verificar Status do Equipamento")
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

        # Banner de Alerta Registrado (Exibido abaixo do botão quando o patrimônio possuir alerta)
        self.alert_banner = QLabel()
        self.alert_banner.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #ffb74d;
                background-color: #3a2800;
                border: 1px solid #ff9800;
                border-radius: 6px;
                padding: 8px 12px;
                margin-top: 2px;
            }
        """)
        self.alert_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alert_banner.setWordWrap(True)
        top_layout.addWidget(self.alert_banner)
        self.alert_banner.setVisible(False)

        # Campo Destino Gerado
        self.hostname_display = QLabel("Destino Gerado: ")
        self.hostname_display.setTextFormat(Qt.TextFormat.RichText)
        self.hostname_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.hostname_display.setStyleSheet("""
            font-size: 17px; 
            font-weight: bold; 
            color: #207bc1; 
            background-color: #3a3a3a;
            border: 1px solid #4d4d4d;
            border-radius: 8px;
            padding: 12px 10px 14px 10px;
            min-height: 75px;
            margin-top: 5px;
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
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        bottom_layout.setSpacing(5)

        # Área de Status
        status_label = QLabel("Status do Execução / Logs:")
        bottom_layout.addWidget(status_label)
        
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.log_panel.setPlaceholderText("Aguardando ação...")
        self.log_panel.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.log_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        bottom_layout.addWidget(self.log_panel, 1)

        self.copy_buttons_layout = QHBoxLayout()
        
        self.copy_ip_button = QPushButton("📋 Copiar IP")
        self.copy_ip_button.setObjectName("CopyIPButton")
        self.copy_ip_button.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #e0e0e0;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
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
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
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
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.splitter)

    def update_completer(self):
        """Atualiza a lista de sugestões do autocompletar."""
        suggestions = history_manager.get_suggestions()
        model = QStringListModel(suggestions)
        self.completer.setModel(model)

    def open_history_dialog(self):
        """Abre o diálogo popup de histórico de acessos."""
        self.active_history_dialog = HistoryDialog(self)
        self.active_history_dialog.item_selected.connect(self.on_history_item_selected)
        self.active_history_dialog.exec()
        self.update_hostname()

    def on_history_item_selected(self, prefix: str, patrimony: str):
        """Aplica a seleção do histórico nos campos da janela principal."""
        if prefix == "HUB-WK":
            self.btn_wk.setChecked(True)
            self.on_type_selected(self.btn_wk)
        elif prefix == "HUB-MD":
            self.btn_md.setChecked(True)
            self.on_type_selected(self.btn_md)
        elif prefix == "HUB-NT":
            self.btn_nt.setChecked(True)
            self.on_type_selected(self.btn_nt)

        self.patrimony_input.setText(patrimony)
        self.update_hostname()

    def on_action_type_changed(self, button):
        is_opt = (button == self.btn_action_opt)
        is_printer = (button == self.btn_action_printer)

        self.printer_path_container.setVisible(is_printer)
        self.cards_widget.setVisible(True)
        self.type_label.setVisible(True)
        self.patrimony_container.setVisible(True)
        self.verify_button.setVisible(True)

        if is_opt:
            self.action_button.setText("Iniciar Painel de Otimização")
        else:
            self.action_button.setText("Executar Conexão")
        
        self.update_hostname()

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

            # Verifica se o equipamento possui alerta em history_manager
            alert_info = history_manager.get_alert(hostname)
            if alert_info and alert_info.get("note"):
                note = alert_info.get("note")
                self.alert_banner.setText(f"⚠️ ALERTA REGISTRADO: \"{note}\"")
                self.alert_banner.setVisible(True)
            else:
                self.alert_banner.setVisible(False)

            self.hostname_display.setText(f"Destino Pronto para Conexão:<br>{hostname}")
            self.action_button.setEnabled(True)
            self.verify_button.setEnabled(True)
            self.copy_hostname_button.setEnabled(True)
            self.inspect_button.setEnabled(True)
        else:
            self.alert_banner.setVisible(False)
            self.hostname_display.setText("Destino Gerado: ")
            self.action_button.setEnabled(False)
            self.verify_button.setEnabled(False)
            self.copy_hostname_button.setEnabled(False)
            self.inspect_button.setEnabled(False)

    def append_status(self, text: str):
        if not text:
            return
            
        # Filtrar linhas de ruído geradas pelo PsExec
        noise_keywords = [
            "PsExec v2.", "Copyright (C)", "Sysinternals -", 
            "Connecting to local system...", "Starting PSEXESVC", 
            "Copying authentication key", "Connecting with PsExec",
            "Starting cmd", "Starting reg", "Starting powershell", 
            "Starting wmic", "Starting net", "exited on"
        ]
        
        if any(keyword in text for keyword in noise_keywords):
            return
            
        self.log_panel.append(f"> {text}")
        self.log_panel.moveCursor(QTextCursor.MoveOperation.End)
        scrollbar = self.log_panel.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_inspect_clicked(self):
        patrimony = self.patrimony_input.text()
        if not self.selected_prefix or not patrimony.strip():
            QMessageBox.warning(self, "Aviso", "Por favor, selecione o tipo de equipamento e insira o patrimônio.")
            return

        hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
        self.inspect_button.setEnabled(False)
        self.action_button.setEnabled(False)
        self.verify_button.setEnabled(False)

        self.log_panel.clear()
        self.append_status(f"Iniciando varredura e identificação de impressoras em {hostname}...")
        self.inspect_thread = PrinterInspectionTask(hostname)
        self.inspect_thread.output_ready.connect(self.append_status)
        self.inspect_thread.finished.connect(self.on_inspection_finished)
        self.inspect_thread.start()

    def on_inspection_finished(self, success, message):
        self.append_status(message)
        self.inspect_button.setEnabled(True)
        self.action_button.setEnabled(True)
        self.verify_button.setEnabled(True)

    def on_verify_clicked(self):
        patrimony = self.patrimony_input.text().strip()
        if not self.selected_prefix or not patrimony:
            return
            
        hostname = HostnameBuilder.build(self.selected_prefix, patrimony)

        # Inclusão no histórico realizada automaticamente ao clicar no botão verifica status
        history_manager.add_entry(self.selected_prefix, patrimony, hostname)
        self.update_completer()

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

            # Atualiza IP no diálogo de otimização se ele já estiver aberto
            if hasattr(self, 'opt_dialog') and self.opt_dialog and self.opt_dialog.isVisible():
                if getattr(self.opt_dialog, 'hostname', None) == hostname and ip_address:
                    self.opt_dialog.ip_address = ip_address
                    if hasattr(self.opt_dialog, 'lbl_ip'):
                        self.opt_dialog.lbl_ip.set_value(ip_address)

            # Dispara busca de usuário ativo em segundo plano
            self.user_task = ActiveUserTask(hostname)
            self.user_task.finished.connect(self.on_active_user_found)
            self.user_task.start()
        else:
            status_html = "<span style='color: #F44336;'>🔴 Inativo</span>"
            self.copy_ip_button.setEnabled(False)
            self.copy_log_button.setEnabled(False)
            if self.pending_open_opt_dialog:
                self.pending_open_opt_dialog = False
                QMessageBox.warning(self, "Equipamento Inativo", f"O equipamento {hostname} não respondeu ao ping na rede.")
            
        self.hostname_display.setText(f"Destino Pronto para Conexão:<br>{hostname} &nbsp; {status_html}")

    def on_active_user_found(self, hostname: str, user_str: str):
        """Atualiza a informação do usuário ativo na tela principal e no histórico."""
        history_manager.update_active_user(hostname, user_str)

        # Atualiza a tela principal se o hostname atual for o mesmo consultado
        patrimony = self.patrimony_input.text().strip()
        current_hostname = HostnameBuilder.build(self.selected_prefix, patrimony) if self.selected_prefix and patrimony else ""

        if current_hostname == hostname:
            status_html = "<span style='color: #4CAF50;'>🟢 Ativo</span>"
            user_color = "#ffb74d" if "Múltiplos" in user_str else ("#81c784" if user_str != "Usuário não encontrado" else "#bbbbbb")
            user_html = f"<br><span style='color: {user_color}; font-size: 14px;'>👤 Usuário Ativo: {user_str}</span>"
            self.hostname_display.setText(f"Destino Pronto para Conexão:<br>{hostname} &nbsp; {status_html}{user_html}")

        if hasattr(self, 'active_history_dialog') and self.active_history_dialog and self.active_history_dialog.isVisible():
            self.active_history_dialog.load_data()

        # Se o diálogo de otimização estiver visível, atualiza as informações do usuário ativo no cabeçalho
        if hasattr(self, 'opt_dialog') and self.opt_dialog and self.opt_dialog.isVisible():
            if getattr(self.opt_dialog, 'hostname', None) == hostname:
                if user_str:
                    self.opt_dialog.active_user = user_str
                    if hasattr(self.opt_dialog, 'lbl_user'):
                        self.opt_dialog.lbl_user.set_value(user_str)
                    self.opt_dialog.selected_target_user = self.opt_dialog._extract_initial_user(user_str)
                    if hasattr(self.opt_dialog, 'lbl_selected_user_target'):
                        self.opt_dialog.lbl_selected_user_target.setText(
                            f"<span style='color: #e0e0e0; font-weight: bold;'>Usuário Alvo:</span> <span style='color: #ffb74d; font-weight: bold;'>{self.opt_dialog.selected_target_user}</span>"
                        )

        # Se houver pendência de abertura do Painel de Otimização (Encadeamento de Botão)
        if self.pending_open_opt_dialog:
            self.pending_open_opt_dialog = False
            active_user_str = history_manager.get_active_user(hostname) or user_str or "Desconhecido"
            if not hasattr(self, 'opt_dialog') or not self.opt_dialog or not self.opt_dialog.isVisible():
                self.opt_dialog = OptimizationDialog(hostname, self.last_ping_ip, active_user_str, parent=None)
                self.opt_dialog.show()
                self.opt_dialog.raise_()
                self.opt_dialog.activateWindow()

    def on_execute_clicked(self):
        if self.btn_action_opt.isChecked():
            patrimony = self.patrimony_input.text().strip()
            if not self.selected_prefix or not patrimony:
                QMessageBox.warning(self, "Aviso", "Por favor, selecione o tipo de equipamento e insira o patrimônio.")
                return
            
            hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
            history_manager.add_entry(self.selected_prefix, patrimony, hostname)
            self.update_completer()

            active_user_str = history_manager.get_active_user(hostname) or "Não verificado"
            ip_str = self.last_ping_ip or "Não verificado"

            self.log_panel.clear()
            self.append_status(f"Iniciando Painel de Otimização Remota para {hostname}...")

            # Instancia e exibe o Painel de Otimização imediatamente
            self.opt_dialog = OptimizationDialog(hostname, ip_str, active_user_str, parent=None)
            self.opt_dialog.show()
            self.opt_dialog.raise_()
            self.opt_dialog.activateWindow()

            # Dispara busca de IP/Usuário em segundo plano caso ainda não tenha sido consultado
            if not self.last_ping_ip:
                self.pending_open_opt_dialog = True
                self.ping_thread = PingTask(hostname)
                self.ping_thread.output_ready.connect(self.append_status)
                self.ping_thread.finished.connect(self.on_ping_finished)
                self.ping_thread.start()
            return

        patrimony = self.patrimony_input.text()
        
        if not self.selected_prefix:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um tipo de equipamento.")
            return
            
        if not patrimony.strip():
            QMessageBox.warning(self, "Aviso", "Por favor, insira o número do patrimônio.")
            return

        hostname = HostnameBuilder.build(self.selected_prefix, patrimony)
        
        self.action_button.setEnabled(False)
        self.verify_button.setEnabled(False)
        
        if self.btn_action_printer.isChecked():
            self.log_panel.clear()
            self.append_status(f"Iniciando conexão de impressora em {hostname}...")
            self.printer_thread = ShortcutPrinterTask(hostname)
            self.printer_thread.output_ready.connect(self.append_status)
            self.printer_thread.finished.connect(self.on_automation_finished)
            self.printer_thread.start()
        else:
            # Lógica original: MSRA
            self.append_status(f"Iniciando automação para {hostname}...")
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
        return helper_copy_to_clipboard(text)

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
            self.statusBar().showMessage("Relatório completo copiado!", 3000)
        else:
            self.statusBar().showMessage("Falha ao copiar o relatório.", 3000)
