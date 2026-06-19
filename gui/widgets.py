from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt
from gui.styles import CARD_STYLE

class CardWidget(QPushButton):
    """Botão em formato de card para seleção de tipo de equipamento."""
    def __init__(self, text: str, prefix_value: str, parent=None):
        super().__init__(text, parent)
        self.prefix_value = prefix_value
        self.setCheckable(True)
        self.setStyleSheet(CARD_STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(80)
