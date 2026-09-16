from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QProgressBar, QScrollArea, QGridLayout, QLineEdit
)
from PyQt6.QtCore import Qt
from gui.styles import OPTIMIZATION_STYLE

class StepCardWidget(QFrame):
    """Widget de Card para uma etapa individual de otimização."""
    def __init__(self, step_number: int, title: str, description: str, parent=None):
        super().__init__(parent)
        self.step_number = step_number
        self.setObjectName("StepCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Cabeçalho da Etapa
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"{step_number}. {title}")
        title_label.setObjectName("StepTitle")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.status_label = QLabel("Pendente")
        self.status_label.setObjectName("StepStatus")
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Descrição
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("StepDescription")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Conteúdo Adicional (subcampos personalizados, ex: Hardware)
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 4, 0, 4)
        layout.addLayout(self.content_layout)

        # Barra de Progresso Visível (em 0%)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("StepProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

class OptimizationWidget(QWidget):
    """Widget principal da aba de Otimização do Sistema."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(OPTIMIZATION_STYLE)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 0)
        main_layout.setSpacing(10)

        # Área com rolagem
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(scroll_content)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setSpacing(10)

        # Cabeçalho Principal do Painel
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 10, 12, 10)
        
        title = QLabel("⚡ PAINEL DE OTIMIZAÇÃO DO SISTEMA")
        title.setObjectName("MainTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)

        prog_title_layout = QHBoxLayout()
        prog_title = QLabel("Progresso Geral da Operação:")
        prog_title.setStyleSheet("font-weight: bold; color: #e0e0e0; font-size: 13px;")
        prog_title_layout.addWidget(prog_title)
        
        prog_title_layout.addStretch()

        self.overall_percent_label = QLabel("0%")
        self.overall_percent_label.setStyleSheet("font-weight: bold; color: #207bc1; font-size: 13px;")
        prog_title_layout.addWidget(self.overall_percent_label)

        header_layout.addLayout(prog_title_layout)

        self.overall_progress = QProgressBar()
        self.overall_progress.setObjectName("OverallProgressBar")
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setTextVisible(False)
        header_layout.addWidget(self.overall_progress)

        self.cards_layout.addWidget(header_frame)

        # -------------------------------------------------------------
        # CONTAINER 1: Coleta de Informações de Hardware
        # -------------------------------------------------------------
        self.card_hardware = StepCardWidget(
            1, 
            "Coleta de Informações de Hardware", 
            "Identificação dos componentes principais do sistema e análise comparativa de armazenamento."
        )
        
        # Grid para subcampos de hardware
        hw_grid = QGridLayout()
        hw_grid.setSpacing(8)

        lbl_cpu = QLabel("Processador:")
        lbl_cpu.setStyleSheet("color: #207bc1; font-weight: bold; font-size: 11px;")
        self.txt_cpu = QLineEdit()
        self.txt_cpu.setReadOnly(True)
        self.txt_cpu.setText("Aguardando leitura...")
        self.txt_cpu.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)

        lbl_ram = QLabel("Memória RAM:")
        lbl_ram.setStyleSheet("color: #207bc1; font-weight: bold; font-size: 11px;")
        self.txt_ram = QLineEdit()
        self.txt_ram.setReadOnly(True)
        self.txt_ram.setText("Aguardando leitura...")
        self.txt_ram.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)

        hw_grid.addWidget(lbl_cpu, 0, 0)
        hw_grid.addWidget(self.txt_cpu, 0, 1)
        hw_grid.addWidget(lbl_ram, 1, 0)
        hw_grid.addWidget(self.txt_ram, 1, 1)

        self.card_hardware.content_layout.addLayout(hw_grid)

        # Quadro Comparativo de Armazenamento
        storage_frame = QFrame()
        storage_frame.setStyleSheet("""
            QFrame {
                background-color: #1e262c;
                border: 1px solid #207bc1;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        storage_layout = QVBoxLayout(storage_frame)
        storage_layout.setContentsMargins(6, 6, 6, 6)
        storage_layout.setSpacing(4)

        self.lbl_storage_before = QLabel("Espaço livre antes: **** GB")
        self.lbl_storage_before.setStyleSheet("color: #81c784; font-weight: bold; font-size: 12px;")

        self.lbl_storage_after = QLabel("Espaço livre após os procedimentos: **** GB")
        self.lbl_storage_after.setStyleSheet("color: #64b5f6; font-weight: bold; font-size: 12px;")

        storage_layout.addWidget(self.lbl_storage_before)
        storage_layout.addWidget(self.lbl_storage_after)

        self.card_hardware.content_layout.addWidget(storage_frame)
        self.cards_layout.addWidget(self.card_hardware)

        # -------------------------------------------------------------
        # CONTAINER 2: Ajuste das Configurações de Desempenho
        # -------------------------------------------------------------
        self.card_perf = StepCardWidget(
            2,
            "Ajuste das Configurações de Desempenho",
            "Ajustar as configurações visuais do Windows para priorizar o melhor desempenho do sistema."
        )
        self.cards_layout.addWidget(self.card_perf)

        # -------------------------------------------------------------
        # CONTAINER 3: Desfragmentação do Disco
        # -------------------------------------------------------------
        self.card_defrag = StepCardWidget(
            3,
            "Desfragmentação do Disco",
            "Otimização e desfragmentação das unidades de disco rígido e SSD."
        )
        self.cards_layout.addWidget(self.card_defrag)

        # -------------------------------------------------------------
        # CONTAINER 4: Limpeza de Pastas Temporárias
        # -------------------------------------------------------------
        self.card_temp = StepCardWidget(
            4,
            "Limpeza de Pastas Temporárias",
            "Limpeza completa das pastas %temp%, temp e prefetch do sistema."
        )
        self.cards_layout.addWidget(self.card_temp)

        # -------------------------------------------------------------
        # CONTAINER 5: Atualização do Navegador Firefox
        # -------------------------------------------------------------
        self.card_firefox = StepCardWidget(
            5,
            "Atualização do Navegador Firefox",
            "Verificação e atualização para a versão mais recente do Mozilla Firefox."
        )
        self.cards_layout.addWidget(self.card_firefox)

        # -------------------------------------------------------------
        # CONTAINER 6: Desativação de Aplicativos Pesados na Inicialização
        # -------------------------------------------------------------
        self.card_startup = StepCardWidget(
            6,
            "Desativação de Aplicativos Pesados na Inicialização",
            "Desabilitar softwares desnecessários da inicialização do Windows."
        )
        self.cards_layout.addWidget(self.card_startup)

        # -------------------------------------------------------------
        # CONTAINER 7: Desativação de Processos em Segundo Plano
        # -------------------------------------------------------------
        self.card_bg_proc = StepCardWidget(
            7,
            "Desativação de Processos em Segundo Plano",
            "Encerrar serviços e processos em background que consomem recursos sem necessidade."
        )
        self.cards_layout.addWidget(self.card_bg_proc)

        # -------------------------------------------------------------
        # CONTAINER 8: Aplicação de Atualizações do Windows Update
        # -------------------------------------------------------------
        self.card_win_update = StepCardWidget(
            8,
            "Aplicação de Atualizações do Windows Update",
            "Busca e aplicação de atualizações pendentes do sistema operacional Windows."
        )
        self.cards_layout.addWidget(self.card_win_update)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
