import subprocess
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QApplication, QLabel
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QToolTip
from utils.helpers import copy_to_clipboard

class ReportDialog(QDialog):
    """Diálogo popup independente contendo o relatório preenchido do chamado com opção de copiar."""
    def __init__(self, report_text: str, parent=None):
        super().__init__(None)  # Janela independente
        self.report_text = report_text
        self.setWindowTitle("Relatório de Atendimento / Chamado")
        self.setMinimumSize(620, 540)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel#TitleLabel {
                font-size: 15px;
                font-weight: bold;
                color: #64b5f6;
            }
            QTextEdit#ReportTextEdit {
                background-color: #121212;
                color: #e0e0e0;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Segoe UI', monospace;
                font-size: 13px;
                line-height: 1.4;
            }
            QPushButton#CopyReportBtn {
                background-color: #207bc1;
                color: #ffffff;
                border: 1px solid #1a66a0;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#CopyReportBtn:hover {
                background-color: #288cda;
            }
            QPushButton#CloseReportBtn {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#CloseReportBtn:hover {
                background-color: #444444;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        lbl_title = QLabel("📋 Relatório Formatado para Chamado / Ticket")
        lbl_title.setObjectName("TitleLabel")
        layout.addWidget(lbl_title)

        self.txt_report = QTextEdit()
        self.txt_report.setObjectName("ReportTextEdit")
        self.txt_report.setReadOnly(True)
        self.txt_report.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.txt_report.setPlainText(self.report_text)
        layout.addWidget(self.txt_report, 1)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        btn_copy = QPushButton("📋 Copiar para Área de Transferência")
        btn_copy.setObjectName("CopyReportBtn")
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.clicked.connect(self.copy_to_clipboard)
        bottom_layout.addWidget(btn_copy)

        btn_close = QPushButton("✖ Fechar")
        btn_close.setObjectName("CloseReportBtn")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)

    def copy_to_clipboard(self):
        text_to_copy = self.txt_report.toPlainText().strip()
        if copy_to_clipboard(text_to_copy):
            pos = QCursor.pos()
            QToolTip.showText(pos, "✅ Relatório copiado para a Área de Transferência!", self, self.rect(), 2500)
        else:
            pos = QCursor.pos()
            QToolTip.showText(pos, "❌ Falha ao copiar relatório.", self, self.rect(), 2500)

