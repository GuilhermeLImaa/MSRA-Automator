import subprocess
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QFrame, QProgressBar, QPushButton, QTextEdit, QLineEdit, QWidget, QMessageBox,
    QApplication, QToolTip, QInputDialog
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor
from gui.styles import OPTIMIZATION_DIALOG_STYLE
from core.hardware_service import HardwareInspectionTask
from core.performance_service import PerformanceAdjustmentTask
from core.defrag_service import DiskDefragTask
from core.temp_cleanup_service import TempCleanupTask
from core.firefox_service import FirefoxUpdateTask
from core.services_service import ServicesAndUpdatesTask
from core.gpo_service import GPOTask
from gui.report_dialog import ReportDialog
from utils.helpers import copy_to_clipboard


class ClickableCopyLabel(QLabel):
    """Rótulo de texto interativo que muda o cursor para pointer e copia o conteúdo ao ser clicado."""
    def __init__(self, title_prefix: str, raw_value: str, style_color: str, parent=None):
        super().__init__(parent)
        self.title_prefix = title_prefix
        self.raw_value = raw_value
        self.style_color = style_color
        
        self.setObjectName("ClickableCopyLabel")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Clique para copiar ou selecione com o mouse")
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.update_display_text()

    def set_value(self, new_value: str):
        self.raw_value = new_value
        self.update_display_text()

    def update_display_text(self):
        self.setText(f"<span style='color: #e0e0e0; font-weight: bold;'>{self.title_prefix}:</span> <span style='color: {self.style_color}; font-weight: bold;'>{self.raw_value}</span>")


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            val_to_copy = str(self.raw_value).strip()
            copy_to_clipboard(val_to_copy)

            # Feedback visual em ToolTip no cursor do mouse
            pos = QCursor.pos()
            QToolTip.showText(pos, f"✅ Copiado: {val_to_copy}", self, self.rect(), 2000)
            event.accept()
        else:
            super().mousePressEvent(event)


class GridBlockWidget(QFrame):
    """Container individual (bloco do Grid 3x2) para cada procedimento de otimização."""
    def __init__(self, block_id: int, icon: str, title: str, description: str, action_btn_text: str, parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.setObjectName("GridBlock")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Cabeçalho do Bloco: Ícone + Título + Tag Status
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"{icon} {title}")
        title_label.setObjectName("BlockTitle")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.status_tag = QLabel("Pendente")
        self.status_tag.setObjectName("BlockStatusTag")
        header_layout.addWidget(self.status_tag)

        layout.addLayout(header_layout)

        # Descrição do Procedimento
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("BlockDescription")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # ÁREA DE DETALHES/SUBCAMPOS PERSONALIZADOS (ex: Hardware no Bloco 1)
        self.details_container = QWidget()
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.setSpacing(6)
        layout.addWidget(self.details_container)

        # Barra de Progresso Visível (0%)
        progress_layout = QHBoxLayout()
        progress_label = QLabel("Progresso:")
        progress_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #aaaaaa;")
        progress_layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("BlockProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)

        layout.addLayout(progress_layout)

        # Log / Status em tempo real do Bloco
        self.log_output = QTextEdit()
        self.log_output.setObjectName("BlockLogOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.log_output.setPlaceholderText("Aguardando comando de execução...")
        self.log_output.setMaximumHeight(85)
        layout.addWidget(self.log_output)

        # Botões de Ação do Bloco (Executar e Abortar)
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(6)

        self.action_btn = QPushButton(action_btn_text)
        self.action_btn.setObjectName("BlockActionBtn")
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btns_layout.addWidget(self.action_btn, 3)

        self.abort_btn = QPushButton("⏹ Abortar")
        self.abort_btn.setObjectName("BlockAbortBtn")
        self.abort_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.abort_btn.setEnabled(False)
        self.abort_btn.setStyleSheet("""
            QPushButton#BlockAbortBtn {
                background-color: #242424;
                color: #555555;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton#BlockAbortBtn:enabled {
                background-color: #b71c1c;
                color: #ffffff;
                border: 1px solid #d32f2f;
            }
            QPushButton#BlockAbortBtn:enabled:hover {
                background-color: #e53935;
            }
        """)
        btns_layout.addWidget(self.abort_btn, 1)

        layout.addLayout(btns_layout)

    def append_log(self, message: str):
        """Adiciona uma mensagem ao log individual do bloco."""
        self.log_output.append(f"> {message}")
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_progress(self, value: int, status_text: str = None):
        """Atualiza a barra de progresso e o status do bloco."""
        self.progress_bar.setValue(value)
        if status_text:
            self.status_tag.setText(status_text)
            if status_text.startswith("Concluído"):
                self.status_tag.setStyleSheet("background-color: #1b5e20; color: #81c784; border: 1px solid #2e7d32;")
            elif status_text == "Em Execução":
                self.status_tag.setStyleSheet("background-color: #0d47a1; color: #64b5f6; border: 1px solid #1976d2;")
            elif status_text == "Erro":
                self.status_tag.setStyleSheet("background-color: #b71c1c; color: #ef9a9a; border: 1px solid #d32f2f;")
            elif "Cancelado" in status_text or "Abortado" in status_text:
                self.status_tag.setStyleSheet("background-color: #424242; color: #ffb74d; border: 1px solid #616161;")


class OptimizationDialog(QDialog):
    """Janela popup maximizada e minimizável em tela cheia com Grid 3x2 de 6 containers de otimização."""
    def __init__(self, hostname: str, ip_address: str = "", active_user: str = "", parent=None):
        super().__init__(None)  # Decoupled window (sem parent/transient) para minimizar e focalizar independentemente
        self.hostname = hostname
        self.ip_address = ip_address or "Não verificado"
        self.active_user = active_user or "Desconhecido"
        self.selected_target_user = self._extract_initial_user(self.active_user)
        self.total_disk_space = "**** GB"
        self.is_running_all = False
        self.execution_queue = []

        # Dicionários de resultados individuais das tarefas (para o gerador de relatórios)
        self.hw_result = {}
        self.perf_result = {}
        self.defrag_result = {}
        self.temp_result = {}
        self.firefox_result = {}
        self.services_result = {}

        self.setWindowTitle(f"Painel de Otimização Remota - {self.hostname}")
        
        # Habilitar botões padrão de Minimizar e Fechar na barra de título
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowMinMaxButtonsHint | 
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self.setStyleSheet(OPTIMIZATION_DIALOG_STYLE)
        
        self.setup_ui()
        self.showMaximized()


    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # -------------------------------------------------------------
        # CABEÇALHO SUPERIOR (Informações da Máquina + Ações Gerais)
        # -------------------------------------------------------------
        top_bar = QFrame()
        top_bar.setObjectName("TopHeaderBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 12, 15, 12)
        top_layout.setSpacing(12)

        # Elementos Clicáveis (Click-to-Copy) no Cabeçalho
        self.lbl_host = ClickableCopyLabel("🖥 Host", self.hostname, "#207bc1")
        self.lbl_ip = ClickableCopyLabel("🌐 IP", self.ip_address, "#81c784")
        self.lbl_user = ClickableCopyLabel("👤 Usuário", self.active_user, "#ffb74d")
        self.lbl_total_space = ClickableCopyLabel("💾 Espaço Total", self.total_disk_space, "#bb86fc")

        top_layout.addWidget(self.lbl_host)
        top_layout.addWidget(self.lbl_ip)
        top_layout.addWidget(self.lbl_user)
        top_layout.addWidget(self.lbl_total_space)

        # Botão Gerar Relatório de Chamado (Posicionado ao lado do Espaço Total, habilitado de início)
        self.btn_generate_report = QPushButton("📋 Gerar Relatório de Chamado")
        self.btn_generate_report.setObjectName("ReportButton")
        self.btn_generate_report.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate_report.setStyleSheet("""
            QPushButton#ReportButton {
                background-color: #2b2b2b;
                color: #ffb74d;
                border: 1px solid #ffb74d;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#ReportButton:hover {
                background-color: #ffb74d;
                color: #121212;
            }
        """)
        self.btn_generate_report.clicked.connect(self.open_report_dialog)
        top_layout.addWidget(self.btn_generate_report)

        # Botão Atualizar GPO (Posicionado ao lado do botão Gerar Relatório)
        self.btn_update_gpo = QPushButton("🔄 Atualizar GPO")
        self.btn_update_gpo.setObjectName("GPOButton")
        self.btn_update_gpo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update_gpo.setStyleSheet("""
            QPushButton#GPOButton {
                background-color: #2b2b2b;
                color: #64b5f6;
                border: 1px solid #64b5f6;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#GPOButton:hover {
                background-color: #64b5f6;
                color: #121212;
            }
            QPushButton#GPOButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
                border: 1px solid #444444;
            }
        """)
        self.btn_update_gpo.clicked.connect(self.run_gpo_update)
        top_layout.addWidget(self.btn_update_gpo)

        top_layout.addStretch()


        # Botão Executar Todos
        self.btn_run_all = QPushButton("⚡ Executar Todas as Otimizações")
        self.btn_run_all.setObjectName("RunAllButton")
        self.btn_run_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run_all.clicked.connect(self.run_all_optimizations)
        top_layout.addWidget(self.btn_run_all)

        # Botão Fechar
        btn_close = QPushButton("✖ Fechar")
        btn_close.setObjectName("CloseDialogBtn")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        top_layout.addWidget(btn_close)

        main_layout.addWidget(top_bar)

        # -------------------------------------------------------------
        # BARRA DE CREDENCIAIS ADMINISTRATIVAS (REDE)
        # -------------------------------------------------------------
        cred_frame = QFrame()
        cred_frame.setObjectName("CredHeaderFrame")
        cred_frame.setStyleSheet("""
            QFrame#CredHeaderFrame {
                background-color: #17212b;
                border: 1px solid #207bc1;
                border-radius: 6px;
            }
        """)
        cred_layout = QHBoxLayout(cred_frame)
        cred_layout.setContentsMargins(12, 8, 12, 8)
        cred_layout.setSpacing(10)

        lbl_cred_title = QLabel("🔑 <b>Credenciais de Rede (WMI / PowerShell):</b>")
        lbl_cred_title.setStyleSheet("color: #64b5f6; font-size: 11px;")
        cred_layout.addWidget(lbl_cred_title)


        lbl_admin_user = QLabel("Usuário Admin:")
        lbl_admin_user.setStyleSheet("color: #e0e0e0; font-size: 11px; font-weight: bold;")
        cred_layout.addWidget(lbl_admin_user)

        self.txt_admin_user = QLineEdit()
        self.txt_admin_user.setPlaceholderText("ex: DOMINIO\\admin ou .\\Administrador")
        self.txt_admin_user.setStyleSheet("background-color: #121212; color: #ffffff; border: 1px solid #333333; border-radius: 4px; padding: 4px 6px; font-size: 11px; min-width: 180px;")
        cred_layout.addWidget(self.txt_admin_user)

        lbl_admin_pass = QLabel("Senha Admin:")
        lbl_admin_pass.setStyleSheet("color: #e0e0e0; font-size: 11px; font-weight: bold;")
        cred_layout.addWidget(lbl_admin_pass)

        self.txt_admin_pass = QLineEdit()
        self.txt_admin_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_admin_pass.setPlaceholderText("••••••••••••")
        self.txt_admin_pass.setStyleSheet("background-color: #121212; color: #ffffff; border: 1px solid #333333; border-radius: 4px; padding: 4px 6px; font-size: 11px; min-width: 150px;")
        cred_layout.addWidget(self.txt_admin_pass)

        cred_layout.addStretch()

        main_layout.addWidget(cred_frame)

        # -------------------------------------------------------------
        # GRID 3x2 (6 CONTAINERS INDEPENDENTES)
        # -------------------------------------------------------------
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(15)

        # BLOCO 1: Hardware & Armazenamento (Coluna 0, Linha 0)
        self.block_hw = GridBlockWidget(
            1, "💻", "Coleta de Hardware & Armazenamento",
            "Identificação dos componentes do sistema e medição do espaço livre.",
            "🔍 Coletar Hardware & Disco"
        )
        self.setup_hardware_subfields(self.block_hw)
        self.block_hw.action_btn.clicked.connect(lambda: self.execute_single_block(1))
        self.block_hw.abort_btn.clicked.connect(lambda: self.abort_single_block(1))
        self.grid_layout.addWidget(self.block_hw, 0, 0)

        # BLOCO 2: Ajuste de Configurações de Desempenho (Coluna 1, Linha 0)
        self.block_perf = GridBlockWidget(
            2, "⚡", "Ajuste das Configurações de Desempenho",
            "Ajustar efeitos visuais do Windows para priorizar o melhor desempenho.",
            "⚡ Ajustar Desempenho Visual"
        )
        user_sel_layout = QHBoxLayout()
        self.lbl_selected_user_target = QLabel(f"<span style='color: #e0e0e0; font-weight: bold;'>Usuário Alvo:</span> <span style='color: #ffb74d; font-weight: bold;'>{self.selected_target_user}</span>")
        self.lbl_selected_user_target.setStyleSheet("font-size: 11px;")
        user_sel_layout.addWidget(self.lbl_selected_user_target)

        self.btn_select_user = QPushButton("👤 Alterar Usuário")
        self.btn_select_user.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select_user.setStyleSheet("font-size: 10px; padding: 3px 8px; background-color: #2b2b2b; color: #ffb74d; border: 1px solid #ffb74d; border-radius: 4px;")
        self.btn_select_user.clicked.connect(self.select_target_user_dialog)
        user_sel_layout.addWidget(self.btn_select_user)

        self.block_perf.details_layout.addLayout(user_sel_layout)

        lbl_notice = QLabel("ℹ️ Otimização aplicada no registro. Requer logoff do usuário para refletir totalmente na interface gráfica.")
        lbl_notice.setStyleSheet("color: #64b5f6; font-size: 11px; margin-top: 2px;")
        lbl_notice.setWordWrap(True)
        self.block_perf.details_layout.addWidget(lbl_notice)

        self.block_perf.action_btn.clicked.connect(lambda: self.execute_single_block(2))
        self.block_perf.abort_btn.clicked.connect(lambda: self.abort_single_block(2))
        self.grid_layout.addWidget(self.block_perf, 0, 1)

        # BLOCO 3: Desfragmentação & Otimização do Disco (Coluna 2, Linha 0)
        self.block_defrag = GridBlockWidget(
            3, "💾", "Desfragmentação & Otimização do Disco",
            "Otimização e desfragmentação das unidades de armazenamento (HDD/SSD).",
            "💾 Desfragmentar / Otimizar Disco"
        )
        self.lbl_defrag_notice = QLabel("Aguardando início da otimização de disco...")
        self.lbl_defrag_notice.setStyleSheet("color: #64b5f6; font-size: 11px; font-weight: bold; margin-top: 4px;")
        self.lbl_defrag_notice.setWordWrap(True)
        self.block_defrag.details_layout.addWidget(self.lbl_defrag_notice)

        self.block_defrag.action_btn.clicked.connect(lambda: self.execute_single_block(3))
        self.block_defrag.abort_btn.clicked.connect(lambda: self.abort_single_block(3))
        self.grid_layout.addWidget(self.block_defrag, 0, 2)

        # BLOCO 4: Limpeza de Arquivos Temporários (Coluna 0, Linha 1)
        self.block_temp = GridBlockWidget(
            4, "🧹", "Limpeza de Pastas Temporárias",
            "Remoção completa de arquivos de cache e temporários nas pastas %temp%, temp e prefetch.",
            "🧹 Limpar Arquivos Temporários"
        )
        self.block_temp.action_btn.clicked.connect(lambda: self.execute_single_block(4))
        self.block_temp.abort_btn.clicked.connect(lambda: self.abort_single_block(4))
        self.grid_layout.addWidget(self.block_temp, 1, 0)

        # BLOCO 5: Atualização do Mozilla Firefox (Coluna 1, Linha 1)
        self.block_firefox = GridBlockWidget(
            5, "🌐", "Atualização do Navegador Firefox",
            "Verificação e atualização para a versão mais recente e estável do Mozilla Firefox.",
            "🌐 Atualizar Mozilla Firefox"
        )
        self.lbl_firefox_notice = QLabel("Aguardando início da atualização...")
        self.lbl_firefox_notice.setStyleSheet("color: #64b5f6; font-size: 11px; font-weight: bold; margin-top: 4px;")
        self.lbl_firefox_notice.setWordWrap(True)
        self.block_firefox.details_layout.addWidget(self.lbl_firefox_notice)

        self.block_firefox.action_btn.clicked.connect(lambda: self.execute_single_block(5))
        self.block_firefox.abort_btn.clicked.connect(lambda: self.abort_single_block(5))
        self.grid_layout.addWidget(self.block_firefox, 1, 1)

        # BLOCO 6: Otimização de Inicialização, Processos & Updates (Coluna 2, Linha 1)
        self.block_services = GridBlockWidget(
            6, "🚀", "Otimização de Serviços & Updates",
            "Desativação de apps pesados na inicialização, processos em 2º plano e Windows Update.",
            "🚀 Otimizar Processos & Updates"
        )
        self.block_services.action_btn.clicked.connect(lambda: self.execute_single_block(6))
        self.block_services.abort_btn.clicked.connect(lambda: self.abort_single_block(6))
        self.grid_layout.addWidget(self.block_services, 1, 2)

        main_layout.addWidget(grid_widget, 1)

    def _validate_credentials(self) -> tuple[str, str] | None:
        """Obtém e valida os campos de Usuário e Senha Admin. Retorna (user, pass) ou exibe alerta se vazios."""
        admin_user = self.txt_admin_user.text().strip()
        admin_pass = self.txt_admin_pass.text()

        if not admin_user or not admin_pass:
            QMessageBox.warning(
                self,
                "Credenciais Obrigatórias",
                "Por favor, preencha o Usuário Admin e a Senha Admin para executar as operações remotas na rede."
            )
            return None
        return admin_user, admin_pass

    def _validate_credentials_silent(self) -> tuple[str, str] | None:
        """Obtém os campos de Usuário e Senha Admin silenciosamente sem mostrar alerta se vazios."""
        admin_user = self.txt_admin_user.text().strip()
        admin_pass = self.txt_admin_pass.text()
        if not admin_user or not admin_pass:
            return None
        return admin_user, admin_pass

    def setup_hardware_subfields(self, block: GridBlockWidget):
        """Configura os subcampos de Processador, Memória e Espaço em Disco no Bloco 1."""
        hw_layout = QVBoxLayout()
        hw_layout.setSpacing(5)

        # Subcampos Processador e Memória
        grid_fields = QGridLayout()
        grid_fields.setSpacing(6)

        lbl_cpu = QLabel("Processador:")
        lbl_cpu.setStyleSheet("color: #207bc1; font-weight: bold; font-size: 11px;")
        self.txt_cpu = QLineEdit()
        self.txt_cpu.setReadOnly(True)
        self.txt_cpu.setText("Aguardando leitura...")
        self.txt_cpu.setStyleSheet("background-color: #121212; color: #ffffff; border: 1px solid #333333; border-radius: 4px; padding: 4px; font-family: Consolas; font-size: 11px;")

        lbl_ram = QLabel("Memória RAM:")
        lbl_ram.setStyleSheet("color: #207bc1; font-weight: bold; font-size: 11px;")
        self.txt_ram = QLineEdit()
        self.txt_ram.setReadOnly(True)
        self.txt_ram.setText("Aguardando leitura...")
        self.txt_ram.setStyleSheet("background-color: #121212; color: #ffffff; border: 1px solid #333333; border-radius: 4px; padding: 4px; font-family: Consolas; font-size: 11px;")

        grid_fields.addWidget(lbl_cpu, 0, 0)
        grid_fields.addWidget(self.txt_cpu, 0, 1)
        grid_fields.addWidget(lbl_ram, 1, 0)
        grid_fields.addWidget(self.txt_ram, 1, 1)

        hw_layout.addLayout(grid_fields)

        # Comparativo de Armazenamento
        storage_frame = QFrame()
        storage_frame.setStyleSheet("background-color: #17212b; border: 1px solid #207bc1; border-radius: 4px; padding: 4px;")
        storage_layout = QVBoxLayout(storage_frame)
        storage_layout.setContentsMargins(6, 4, 6, 4)
        storage_layout.setSpacing(2)

        self.lbl_storage_before = QLabel("Espaço livre antes: **** GB")
        self.lbl_storage_before.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.lbl_storage_before.setStyleSheet("color: #81c784; font-weight: bold; font-size: 11px;")

        self.lbl_storage_after = QLabel("Espaço livre após os procedimentos: **** GB")
        self.lbl_storage_after.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.lbl_storage_after.setStyleSheet("color: #64b5f6; font-weight: bold; font-size: 11px;")

        storage_layout.addWidget(self.lbl_storage_before)
        storage_layout.addWidget(self.lbl_storage_after)

        hw_layout.addWidget(storage_frame)
        block.details_layout.addLayout(hw_layout)

    def _extract_initial_user(self, user_str: str) -> str:
        """Extrai um nome de usuário inicial limpo a partir da string de usuários ativos."""
        import re
        match = re.search(r'\(([^)]+)\)', user_str)
        if match:
            inside = match.group(1)
            users_list = [u.strip() for u in inside.split(',') if u.strip()]
            if users_list:
                return users_list[0]
        
        clean = user_str.split('\\')[-1].strip()
        if "," in clean:
            clean = clean.split(",")[0].strip()
        clean = clean.replace("Múltiplos", "").replace("multiplos", "").strip()
        return clean or user_str

    def select_target_user_dialog(self):
        """Abre caixa de seleção para o operador escolher o usuário alvo em máquinas com múltiplos usuários."""
        import re
        user_options = []
        match = re.search(r'\(([^)]+)\)', self.active_user)
        if match:
            inside = match.group(1)
            found_users = [u.strip() for u in inside.split(',') if u.strip()]
            for u in found_users:
                if u and u not in user_options:
                    user_options.append(u)
        elif "," in self.active_user or "Múltiplos" in self.active_user or "multiplos" in self.active_user:
            found_users = re.findall(r'[a-zA-Z0-9\._\-]+', self.active_user)
            for u in found_users:
                if u.lower() not in ["múltiplos", "multiplos", "usuário", "ativo", "desconhecido"] and u not in user_options:
                    user_options.append(u)

        if not user_options:
            user_options = [self.selected_target_user]

        dialog = QInputDialog(self)
        dialog.setWindowTitle("Selecionar Usuário Alvo")
        dialog.setLabelText("Escolha qual usuário conectado receberá as alterações no registro:")
        dialog.setComboBoxItems(user_options)
        try:
            idx = user_options.index(self.selected_target_user)
            dialog.setTextValue(user_options[idx])
        except Exception:
            pass
        dialog.setStyleSheet("""
            QInputDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
            }
            QComboBox {
                background-color: #121212;
                color: #ffffff;
                border: 1px solid #207bc1;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                color: #ffffff;
                selection-background-color: #207bc1;
                selection-color: #ffffff;
            }
            QPushButton {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #207bc1;
                border-color: #1a66a0;
            }
        """)

        ok = dialog.exec()
        user = dialog.textValue()

        if ok and user.strip():
            self.selected_target_user = user.strip()
            self.lbl_selected_user_target.setText(f"<span style='color: #e0e0e0; font-weight: bold;'>Usuário Alvo:</span> <span style='color: #ffb74d; font-weight: bold;'>{self.selected_target_user}</span>")
            self.block_perf.append_log(f"Usuário alvo alterado para: '{self.selected_target_user}'")



    def execute_single_block(self, block_id: int):
        """Executa um procedimento individual do grid de forma independente."""
        if block_id == 1:
            self.run_hardware_inspection()
            return
        elif block_id == 2:
            self.run_performance_adjustment()
            return
        elif block_id == 3:
            self.run_disk_defrag()
            return
        elif block_id == 4:
            self.run_temp_cleanup()
            return
        elif block_id == 5:
            self.run_firefox_update()
            return
        elif block_id == 6:
            self.run_services_and_updates()
            return

    def abort_single_block(self, block_id: int):
        """Aborta o procedimento do bloco especificado de forma independente."""
        thread_map = {
            1: ('hw_thread', self.block_hw, "Coleta de Hardware"),
            2: ('perf_thread', self.block_perf, "Ajuste de Desempenho"),
            3: ('defrag_thread', self.block_defrag, "Desfragmentação do Disco"),
            4: ('temp_thread', self.block_temp, "Limpeza de Temporários"),
            5: ('firefox_thread', self.block_firefox, "Atualização do Firefox"),
            6: ('services_thread', self.block_services, "Otimização de Serviços")
        }

        if block_id in thread_map:
            attr_name, block_widget, name = thread_map[block_id]
            if hasattr(self, attr_name):
                thread = getattr(self, attr_name)
                if thread and thread.isRunning():
                    try:
                        thread.requestInterruption()
                        thread.terminate()
                        thread.wait(300)
                    except Exception:
                        pass

            block_widget.append_log(f"⚠️ Operação '{name}' abortada pelo operador.")
            block_widget.update_progress(0, "Cancelado")
            block_widget.action_btn.setEnabled(True)
            block_widget.abort_btn.setEnabled(False)
            self._check_all_finished()

    def run_hardware_inspection(self):
        """Dispara a execução assíncrona da Etapa 1 (Coleta de Hardware)."""
        creds = self._validate_credentials()
        if not creds:
            return
        admin_user, admin_pass = creds

        self.block_hw.action_btn.setEnabled(False)
        self.block_hw.abort_btn.setEnabled(True)
        self.block_hw.log_output.clear()
        self.block_hw.update_progress(5, "Em Execução")
        
        target = self.hostname

        self.hw_thread = HardwareInspectionTask(target, admin_user, admin_pass)
        self.hw_thread.output_ready.connect(self.block_hw.append_log)
        self.hw_thread.progress_updated.connect(self.block_hw.update_progress)
        self.hw_thread.finished_with_result.connect(self.on_hardware_inspection_finished)
        self.hw_thread.start()

    def on_hardware_inspection_finished(self, result: dict):
        """Atualiza a UI com os dados coletados na Etapa 1."""
        self.block_hw.action_btn.setEnabled(True)
        self.block_hw.abort_btn.setEnabled(False)
        self.hw_result = result

        if result.get("success"):
            self.txt_cpu.setText(result.get("cpu_name", "Não identificado"))
            self.txt_ram.setText(result.get("ram_gb", "Não identificado"))
            
            free_gb = result.get("free_space_gb", "****")
            total_gb = result.get("total_space_gb", "****")

            self.lbl_storage_before.setText(f"Espaço livre antes: {free_gb} GB")
            
            if total_gb != "****":
                self.lbl_total_space.set_value(f"{total_gb} GB")

            self.block_hw.update_progress(100, "Concluído")
        else:
            self.block_hw.update_progress(0, "Erro")

        self._check_all_finished()

    def run_performance_adjustment(self):
        """Dispara a execução assíncrona da Etapa 2 (Ajuste de Desempenho)."""
        creds = self._validate_credentials()
        if not creds:
            return
        admin_user, admin_pass = creds

        self.block_perf.action_btn.setEnabled(False)
        self.block_perf.abort_btn.setEnabled(True)
        self.block_perf.log_output.clear()
        self.block_perf.update_progress(5, "Em Execução")

        target = self.hostname

        self.perf_thread = PerformanceAdjustmentTask(target, self.selected_target_user, admin_user, admin_pass)
        self.perf_thread.output_ready.connect(self.block_perf.append_log)
        self.perf_thread.progress_updated.connect(self.block_perf.update_progress)
        self.perf_thread.finished_with_result.connect(self.on_performance_adjustment_finished)
        self.perf_thread.start()

    def on_performance_adjustment_finished(self, result: dict):
        """Atualiza a UI após a conclusão da Etapa 2."""
        self.block_perf.action_btn.setEnabled(True)
        self.block_perf.abort_btn.setEnabled(False)
        self.perf_result = result
        if result.get("success"):
            self.block_perf.update_progress(100, "Concluído")
        else:
            self.block_perf.update_progress(0, "Erro")

        self._check_all_finished()

    def run_disk_defrag(self):
        """Dispara a execução assíncrona da Etapa 3 (Desfragmentação e Otimização do Disco)."""
        creds = self._validate_credentials()
        if not creds:
            return
        admin_user, admin_pass = creds

        self.block_defrag.action_btn.setEnabled(False)
        self.block_defrag.abort_btn.setEnabled(True)
        self.block_defrag.log_output.clear()
        self.block_defrag.update_progress(5, "Em Execução")

        target = self.hostname

        self.defrag_thread = DiskDefragTask(target, admin_user, admin_pass)
        self.defrag_thread.output_ready.connect(self.block_defrag.append_log)
        self.defrag_thread.progress_updated.connect(self.block_defrag.update_progress)
        self.defrag_thread.media_type_detected.connect(self.on_defrag_media_type_detected)
        self.defrag_thread.finished_with_result.connect(self.on_disk_defrag_finished)
        self.defrag_thread.start()

    def on_defrag_media_type_detected(self, media_type: str, notice_msg: str):
        """Atualiza o subtítulo dinâmico do Container 3 ao detectar HDD ou SSD."""
        self.lbl_defrag_notice.setText(notice_msg)
        if media_type == "HDD":
            self.lbl_defrag_notice.setStyleSheet("color: #ffb74d; font-size: 11px; font-weight: bold; margin-top: 4px;")
        else:
            self.lbl_defrag_notice.setStyleSheet("color: #64b5f6; font-size: 11px; font-weight: bold; margin-top: 4px;")

    def on_disk_defrag_finished(self, result: dict):
        """Atualiza a UI após a conclusão da Etapa 3."""
        self.block_defrag.action_btn.setEnabled(True)
        self.block_defrag.abort_btn.setEnabled(False)
        self.defrag_result = result
        if result.get("success"):
            self.lbl_defrag_notice.setText("Unidades de armazenamento otimizadas com sucesso.")
            self.lbl_defrag_notice.setStyleSheet("color: #81c784; font-size: 11px; font-weight: bold; margin-top: 4px;")
            self.block_defrag.update_progress(100, "Concluído")
        else:
            self.block_defrag.update_progress(0, "Erro")

        self._check_all_finished()

    def run_temp_cleanup(self):
        """Dispara a execução assíncrona da Etapa 4 (Limpeza de Pastas Temporárias)."""
        creds = self._validate_credentials()
        if not creds:
            return
        admin_user, admin_pass = creds

        self.block_temp.action_btn.setEnabled(False)
        self.block_temp.abort_btn.setEnabled(True)
        self.block_temp.log_output.clear()
        self.block_temp.update_progress(5, "Em Execução")

        target = self.hostname

        self.temp_thread = TempCleanupTask(target, self.active_user, admin_user, admin_pass)
        self.temp_thread.output_ready.connect(self.block_temp.append_log)
        self.temp_thread.progress_updated.connect(self.block_temp.update_progress)
        self.temp_thread.finished_with_result.connect(self.on_temp_cleanup_finished)
        self.temp_thread.start()

    def on_temp_cleanup_finished(self, result: dict):
        """Atualiza a UI após a conclusão da Etapa 4."""
        self.block_temp.action_btn.setEnabled(True)
        self.block_temp.abort_btn.setEnabled(False)
        self.temp_result = result
        if result.get("success"):
            count = result.get("deleted_files_count", 0)
            if count > 0:
                fmt_cnt = f"{count:,}".replace(",", ".")
                self.block_temp.append_log(f"📊 Arquivos removidos nesta sessão: {fmt_cnt} arquivos.")
                self.block_temp.update_progress(100, f"Concluído ({fmt_cnt} apagados)")
            else:
                self.block_temp.update_progress(100, "Concluído")
            self.check_post_cleanup_storage()
        else:
            self.block_temp.update_progress(0, "Erro")

        self._check_all_finished()

    def check_post_cleanup_storage(self):
        """Dispara medição pós-limpeza do espaço livre em disco."""
        creds = self._validate_credentials_silent()
        if not creds:
            return
        admin_user, admin_pass = creds
        self.post_hw_thread = HardwareInspectionTask(self.hostname, admin_user, admin_pass)
        self.post_hw_thread.finished_with_result.connect(self.on_post_storage_finished)
        self.post_hw_thread.start()

    def on_post_storage_finished(self, result: dict):
        if result.get("success"):
            free_after = result.get("free_space_gb", "****")
            if free_after != "****":
                self.hw_result["free_space_after"] = free_after
                self.lbl_storage_after.setText(f"Espaço livre após os procedimentos: {free_after} GB")

    def run_firefox_update(self):
        """Dispara a execução assíncrona da Etapa 5 (Atualização do Firefox)."""
        creds = self._validate_credentials()
        if not creds:
            return
        admin_user, admin_pass = creds

        self.block_firefox.action_btn.setEnabled(False)
        self.block_firefox.abort_btn.setEnabled(True)
        self.block_firefox.log_output.clear()
        self.block_firefox.update_progress(20, "Fazendo download da última versão...")

        target = self.hostname

        self.firefox_thread = FirefoxUpdateTask(target, admin_user, admin_pass)
        self.firefox_thread.output_ready.connect(self.block_firefox.append_log)
        self.firefox_thread.progress_updated.connect(self.block_firefox.update_progress)
        self.firefox_thread.finished_with_result.connect(self.on_firefox_update_finished)
        self.firefox_thread.start()

    def on_firefox_update_finished(self, result: dict):
        """Atualiza a UI após a conclusão da Etapa 5."""
        self.block_firefox.action_btn.setEnabled(True)
        self.block_firefox.abort_btn.setEnabled(False)
        self.firefox_result = result
        if result.get("success"):
            self.lbl_firefox_notice.setText("Firefox atualizado para a versão mais recente com sucesso.")
            self.lbl_firefox_notice.setStyleSheet("color: #81c784; font-size: 11px; font-weight: bold; margin-top: 4px;")
            self.block_firefox.update_progress(100, "Concluído")
        else:
            self.block_firefox.update_progress(0, "Erro")

        self._check_all_finished()

    def run_services_and_updates(self):
        """Dispara a execução assíncrona da Etapa 6 (Otimização de Serviços & Updates)."""
        creds = self._validate_credentials()
        if not creds:
            return
        admin_user, admin_pass = creds

        self.block_services.action_btn.setEnabled(False)
        self.block_services.abort_btn.setEnabled(True)
        self.block_services.log_output.clear()
        self.block_services.update_progress(10, "Em Execução")

        target = self.hostname

        self.services_thread = ServicesAndUpdatesTask(target, self.selected_target_user, admin_user, admin_pass)
        self.services_thread.output_ready.connect(self.block_services.append_log)
        self.services_thread.progress_updated.connect(self.block_services.update_progress)
        self.services_thread.finished_with_result.connect(self.on_services_finished)
        self.services_thread.start()

    def on_services_finished(self, result: dict):
        """Atualiza a UI após a conclusão da Etapa 6."""
        self.block_services.action_btn.setEnabled(True)
        self.block_services.abort_btn.setEnabled(False)
        self.services_result = result
        if result.get("success"):
            self.block_services.update_progress(100, "Concluído")
        else:
            self.block_services.update_progress(0, "Erro")

        self._check_all_finished()

    def _check_all_finished(self):
        """Verifica se todas as tarefas ativas foram concluídas para restaurar o botão Executar Todos."""
        active_threads = [
            getattr(self, 'hw_thread', None),
            getattr(self, 'perf_thread', None),
            getattr(self, 'defrag_thread', None),
            getattr(self, 'temp_thread', None),
            getattr(self, 'firefox_thread', None),
            getattr(self, 'services_thread', None)
        ]
        running = any(t and t.isRunning() for t in active_threads)
        if not running:
            self.btn_run_all.setEnabled(True)
            self.btn_run_all.setText("⚡ Executar Todas as Otimizações")

    def run_all_optimizations(self):
        """Executa todos os 6 procedimentos de otimização simultaneamente de uma só vez."""
        creds = self._validate_credentials()
        if not creds:
            return

        self.btn_run_all.setEnabled(False)
        self.btn_run_all.setText("⚡ Otimizações em Execução Simultânea...")

        # Dispara todas as 6 tarefas simultaneamente em paralelo
        for block_id in range(1, 7):
            self.execute_single_block(block_id)

    def open_report_dialog(self):
        """Abre o QDialog de relatório preenchido dinamicamente com os resultados das etapas."""
        report_text = self.generate_report_text()
        self.active_report_dialog = ReportDialog(report_text, parent=None)
        self.active_report_dialog.show()

    def run_gpo_update(self):
        """Dispara a atualização remota de GPO (gpupdate /force) via GPOTask."""
        creds = self._validate_credentials()
        if not creds:
            return
        admin_user, admin_pass = creds

        self.btn_update_gpo.setEnabled(False)
        self.btn_update_gpo.setText("⏳ Atualizando...")

        target = self.hostname

        self.gpo_thread = GPOTask(target, admin_user, admin_pass)
        self.gpo_thread.finished.connect(self.on_gpo_update_finished)
        self.gpo_thread.start()

    def on_gpo_update_finished(self, log_output: str):
        """Restaura o botão de GPO ao estado normal e exibe o log numa caixa QMessageBox.information."""
        self.btn_update_gpo.setEnabled(True)
        self.btn_update_gpo.setText("🔄 Atualizar GPO")

        QMessageBox.information(
            self,
            "Resultado da Atualização de GPO",
            log_output
        )

    def generate_report_text(self) -> str:
        """Gera o texto do relatório formatado segundo as variáveis dinâmicas e checkmarks."""
        import re

        # 1. Variáveis de Hardware
        var_cpu = self.txt_cpu.text().strip() if hasattr(self, 'txt_cpu') and self.txt_cpu.text() and self.txt_cpu.text() != "Aguardando leitura..." else self.hw_result.get("cpu_name", "Não identificado")
        var_ram = self.txt_ram.text().strip() if hasattr(self, 'txt_ram') and self.txt_ram.text() and self.txt_ram.text() != "Aguardando leitura..." else self.hw_result.get("ram_gb", "Não identificado")
        
        var_total_space = self.hw_result.get("total_space_gb", "****")
        if var_total_space == "****" and hasattr(self, 'lbl_total_space'):
            raw_sp = str(self.lbl_total_space.raw_value).replace("GB", "").strip()
            if raw_sp != "****":
                var_total_space = raw_sp

        var_free_before = self.hw_result.get("free_space_gb", "****")
        if var_free_before == "****" and hasattr(self, 'lbl_storage_before'):
            txt_b = self.lbl_storage_before.text()
            m = re.search(r'Espaço livre antes:\s*([\d\.\*]+)\s*GB', txt_b)
            if m:
                var_free_before = m.group(1).strip()

        # Espaço livre após os procedimentos: se a limpeza rodou ou a pós-medição está disponível
        var_free_after = self.hw_result.get("free_space_after", "****")
        if var_free_after == "****" and hasattr(self, 'lbl_storage_after'):
            txt_a = self.lbl_storage_after.text()
            m_a = re.search(r'Espaço livre após os procedimentos:\s*([\d\.\*]+)\s*GB', txt_a)
            if m_a and m_a.group(1).strip() != "****":
                var_free_after = m_a.group(1).strip()

        if var_free_after == "****":
            var_free_after = var_free_before

        # 2. Checkmarks (✔️ apenas se success == True)
        var_check_desempenho = "✔️" if self.perf_result.get("success") else ""
        var_check_disco = "✔️" if self.defrag_result.get("success") else ""
        var_check_temp = "✔️" if self.temp_result.get("success") else ""
        var_check_firefox = "✔️" if self.firefox_result.get("success") else ""
        var_check_startup = "✔️" if self.services_result.get("success") else ""

        template = f"""Prezados Senhores,
Informações de hardware coletadas:

Processador: {var_cpu}
Memória: {var_ram}
Armazenamento total: {var_total_space} GB
Espaço livre antes: {var_free_before} GB
Espaço livre após os procedimentos: {var_free_after} GB

Procedimentos realizados para correção da lentidão:

Ajuste das configurações de desempenho {var_check_desempenho}
Desfragmentação do disco {var_check_disco}
Limpeza de pastas temporárias (%temp%, temp e prefetch) {var_check_temp}
Atualização do navegador Firefox {var_check_firefox}
Desativação de aplicativos pesados na inicialização do sistema operacional {var_check_startup}
Desativação de aplicativos em segundo plano (processos do sistema) {var_check_startup}
Aplicação de atualizações do Windows Update {var_check_startup}

Orientamos a acionar novamente o suporte técnico caso o equipamento mantenha comportamento lento após as correções remotas, para que sejam realizados novos procedimentos presenciais (in loco), se necessário.

A equipe de suporte técnico permanece à disposição para quaisquer esclarecimentos adicionais.

Atenciosamente,
Equipe de Suporte Técnico – SETISD"""

        return template

        self._run_next_queued_task()
