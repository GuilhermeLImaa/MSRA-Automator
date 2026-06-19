from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon

def confirm_execution(parent, hostname: str) -> bool:
    """Exibe um diálogo de confirmação antes de rodar o MSRA."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle("Confirmação de Conexão")
    msg.setText(f"Deseja iniciar a Assistência Remota (MSRA) para:\n\n{hostname}")
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.No)
    
    # Customizando botões para português
    msg.button(QMessageBox.StandardButton.Yes).setText("Sim, conectar")
    msg.button(QMessageBox.StandardButton.No).setText("Cancelar")
    
    # Estilizando levemente para dark theme
    msg.setStyleSheet("QMessageBox { background-color: #1e1e1e; color: #ffffff; } QLabel { color: #ffffff; } QPushButton { background-color: #333333; color: #ffffff; padding: 5px 15px; border-radius: 4px; }")
    
    result = msg.exec()
    return result == QMessageBox.StandardButton.Yes
