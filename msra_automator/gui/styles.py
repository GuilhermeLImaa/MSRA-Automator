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

QRadioButton {
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-weight: bold;
    font-size: 13px;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid #555555;
    background-color: #3a3a3a;
}

QRadioButton::indicator:hover {
    border-color: #207bc1;
}

QRadioButton::indicator:checked {
    background-color: #207bc1;
    border-color: #1a66a0;
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

SEGMENTED_BUTTON_STYLE = """
QFrame#SegmentedContainer {
    background-color: #242424;
    border: 1px solid #444444;
    border-radius: 6px;
}

QPushButton#SegmentButton {
    background-color: transparent;
    color: #207bc1;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#SegmentButton:hover {
    background-color: #333333;
    color: #389bed;
}

QPushButton#SegmentButton:checked {
    background-color: #1a5c8e;
    color: #ffffff;
    border: none;
}
"""

OPTIMIZATION_STYLE = """
QFrame#HeaderFrame {
    background-color: #1e1e1e;
    border: 1px solid #4d4d4d;
    border-radius: 8px;
}

QLabel#MainTitle {
    font-size: 15px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 4px;
}

QProgressBar#OverallProgressBar {
    background-color: #2a2a2a;
    border: 1px solid #444444;
    border-radius: 5px;
    height: 10px;
}

QProgressBar#OverallProgressBar::chunk {
    background-color: #207bc1;
    border-radius: 4px;
}

QFrame#StepCard {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
}

QFrame#StepCard:hover {
    border: 1px solid #207bc1;
}

QLabel#StepTitle {
    font-size: 13px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#StepStatus {
    font-size: 11px;
    font-weight: bold;
    color: #888888;
    background-color: #2a2a2a;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #444444;
}

QLabel#StepDescription {
    font-size: 11px;
    color: #aaaaaa;
}

QProgressBar#StepProgressBar {
    background-color: #2a2a2a;
    border: 1px solid #444444;
    border-radius: 4px;
    height: 14px;
    text-align: center;
    color: #ffffff;
    font-size: 10px;
    font-weight: bold;
}

QProgressBar#StepProgressBar::chunk {
    background-color: #207bc1;
    border-radius: 3px;
}
"""

OPTIMIZATION_DIALOG_STYLE = """
QDialog {
    background-color: #1a1a1a;
    color: #ffffff;
}

QLabel {
    color: #e0e0e0;
}

QFrame#TopHeaderBar {
    background-color: #242424;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
}


QPushButton#RunAllButton {
    background-color: #207bc1;
    color: #ffffff;
    border: 1px solid #1a66a0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
}

QPushButton#RunAllButton:hover {
    background-color: #288cda;
    border: 1px solid #207bc1;
}

QPushButton#CloseDialogBtn {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: bold;
}

QPushButton#CloseDialogBtn:hover {
    background-color: #d32f2f;
    border: 1px solid #f44336;
}

QFrame#GridBlock {
    background-color: #222222;
    border: 1px solid #383838;
    border-radius: 10px;
}

QFrame#GridBlock:hover {
    border: 1px solid #207bc1;
}

QLabel#BlockTitle {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#BlockStatusTag {
    font-size: 11px;
    font-weight: bold;
    color: #aaaaaa;
    background-color: #2d2d2d;
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid #444444;
}

QLabel#BlockDescription {
    font-size: 12px;
    color: #bbbbbb;
}

QProgressBar#BlockProgressBar {
    background-color: #141414;
    border: 1px solid #444444;
    border-radius: 5px;
    height: 16px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
    font-weight: bold;
}

QProgressBar#BlockProgressBar::chunk {
    background-color: #207bc1;
    border-radius: 4px;
}

QTextEdit#BlockLogOutput {
    background-color: #121212;
    color: #64b5f6;
    border: 1px solid #333333;
    border-radius: 5px;
    padding: 6px;
    font-family: 'Consolas', monospace;
    font-size: 11px;
}

QPushButton#BlockActionBtn {
    background-color: #2b2b2b;
    color: #207bc1;
    border: 1px solid #207bc1;
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton#BlockActionBtn:hover {
    background-color: #1a5c8e;
    color: #ffffff;
    border: 1px solid #288cda;
}

QPushButton#BlockActionBtn:disabled {
    background-color: #1c1c1c;
    color: #555555;
    border: 1px solid #333333;
}

QLabel#ClickableCopyLabel {
    padding: 4px 8px;
    border-radius: 4px;
    background-color: #1a1a1a;
    border: 1px solid #333333;
    color: #ffffff;
}

QLabel#ClickableCopyLabel:hover {
    background-color: #333333;
    border: 1px solid #207bc1;
    color: #ffffff;
}
"""





