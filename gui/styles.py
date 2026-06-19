# Estilos modernos para a aplicação PyQt6, baseados no tema do IOS app

MAIN_STYLE = """
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QLabel {
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-weight: bold;
}

QLineEdit {
    background-color: #3a3a3a;
    border: 1px solid #4d4d4d;
    border-radius: 5px;
    padding: 8px;
    color: #ffffff;
    font-size: 14px;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QLineEdit:focus {
    border: 1px solid #207bc1;
    background-color: #404040;
}

QPushButton#ActionButton {
    background-color: #207bc1;
    color: white;
    border: 1px solid #1a66a0;
    border-radius: 5px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#ActionButton:hover {
    background-color: #288cda;
    border: 1px solid #207bc1;
}

QPushButton#ActionButton:disabled {
    background-color: #444444;
    border: 1px solid #333333;
    color: #888888;
}

QTextEdit {
    background-color: #1e1e1e;
    color: #cccccc;
    border: 1px solid #333333;
    border-radius: 5px;
    padding: 8px;
    font-family: 'Consolas', monospace;
    font-size: 12px;
}

QSplitter::handle {
    background-color: #444444;
    border: 1px solid #333333;
}

QSplitter::handle:vertical {
    height: 6px;
}

QSplitter::handle:hover {
    background-color: #207bc1;
}

QStatusBar {
    background-color: #222222;
    color: #888888;
    font-size: 12px;
}

"""

CARD_STYLE = """
QPushButton {
    background-color: #3a3a3a;
    border: 1px solid #4d4d4d;
    border-radius: 6px;
    padding: 15px;
    color: #e0e0e0;
    font-size: 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #444444;
    border: 1px solid #5a5a5a;
}

QPushButton:checked {
    background-color: #207bc1;
    color: #ffffff;
    border: 1px solid #1a66a0;
}
"""
