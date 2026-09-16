from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QWidget, QSplitter,
    QMessageBox, QInputDialog, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor
from core.history_manager import history_manager

class HistoryDialog(QDialog):
    item_selected = pyqtSignal(str, str) # Emite (prefix, patrimony)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico de Acessos, Favoritos e Alertas")
        self.resize(1040, 600)
        self.setMinimumSize(960, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #242424;
                color: #ffffff;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 6px;
                color: #ffffff;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 6px;
                color: #ffffff;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #2b2b2b;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 4px;
            }
            QListWidget::item:hover {
                background-color: #383838;
                border-color: #207bc1;
            }
            QListWidget::item:selected {
                background-color: #1a5c8e;
                border-color: #207bc1;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                border-radius: 6px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #bbbbbb;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
                border-bottom: 2px solid #207bc1;
            }
        """)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # -------------------------------------------------------------
        # PAINEL ESQUERDO: HISTÓRICO DE ACESSOS
        # -------------------------------------------------------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)

        left_header = QLabel("🕒 Histórico de Acessos")
        left_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #207bc1;")
        left_layout.addWidget(left_header)

        # Campo de busca no histórico
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar no histórico...")
        self.search_input.textChanged.connect(self.filter_history)
        left_layout.addWidget(self.search_input)

        # Scroll Area com lista customizada de cards de histórico
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #333333;
                border-radius: 6px;
                background-color: #1e1e1e;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #1e1e1e;
            }
        """)
        self.history_scroll.viewport().setStyleSheet("background-color: #1e1e1e;")

        self.history_container = QWidget()
        self.history_container.setStyleSheet("background-color: #1e1e1e;")
        self.history_container_layout = QVBoxLayout(self.history_container)
        self.history_container_layout.setContentsMargins(8, 8, 8, 8)
        self.history_container_layout.setSpacing(8)
        self.history_container_layout.addStretch()

        self.history_scroll.setWidget(self.history_container)
        left_layout.addWidget(self.history_scroll)

        splitter.addWidget(left_widget)

        # -------------------------------------------------------------
        # PAINEL DIREITO: FAVORITOS E ALERTAS (Com botões de setas ▲/▼)
        # -------------------------------------------------------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)

        right_header = QLabel("Favoritos / Alertas (Use ▲ e ▼ para Reordenar)")
        right_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0;")
        right_layout.addWidget(right_header)

        self.tab_widget = QTabWidget()

        # ABA FAVORITOS
        self.fav_tab = QWidget()
        fav_layout = QVBoxLayout(self.fav_tab)
        fav_layout.setContentsMargins(8, 8, 8, 8)

        self.fav_list = QListWidget()
        self.fav_list.itemDoubleClicked.connect(self.on_fav_item_double_clicked)
        fav_layout.addWidget(self.fav_list)

        fav_btns_layout = QHBoxLayout()
        
        btn_fav_up = QPushButton("▲ Mover P/ Cima")
        btn_fav_up.setStyleSheet("background-color: #2e3a4e; color: #64b5f6; border: 1px solid #1e88e5; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn_fav_up.clicked.connect(self.move_favorite_up)

        btn_fav_down = QPushButton("▼ Mover P/ Baixo")
        btn_fav_down.setStyleSheet("background-color: #2e3a4e; color: #64b5f6; border: 1px solid #1e88e5; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn_fav_down.clicked.connect(self.move_favorite_down)

        btn_remove_fav = QPushButton("❌ Remover")
        btn_remove_fav.setStyleSheet("background-color: #3a2222; color: #ff8888; border: 1px solid #552222; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn_remove_fav.clicked.connect(self.remove_selected_favorite)
        
        btn_edit_fav_user = QPushButton("✏️ Editar Usuário")
        btn_edit_fav_user.setToolTip("Editar / Definir nome do usuário ativo do favorito selecionado")
        btn_edit_fav_user.setStyleSheet("background-color: #2b3a2b; color: #81c784; border: 1px solid #388e3c; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn_edit_fav_user.clicked.connect(self.edit_selected_favorite_user)

        fav_btns_layout.addWidget(btn_fav_up)
        fav_btns_layout.addWidget(btn_fav_down)
        fav_btns_layout.addWidget(btn_edit_fav_user)
        fav_btns_layout.addWidget(btn_remove_fav)
        fav_layout.addLayout(fav_btns_layout)

        self.tab_widget.addTab(self.fav_tab, "⭐ Favoritos")

        # ABA ALERTAS
        self.alert_tab = QWidget()
        alert_layout = QVBoxLayout(self.alert_tab)
        alert_layout.setContentsMargins(8, 8, 8, 8)

        self.alert_list = QListWidget()
        self.alert_list.itemDoubleClicked.connect(self.on_alert_item_double_clicked)
        alert_layout.addWidget(self.alert_list)

        alert_btns_layout = QHBoxLayout()

        btn_alert_up = QPushButton("▲ Mover P/ Cima")
        btn_alert_up.setStyleSheet("background-color: #2e3a4e; color: #64b5f6; border: 1px solid #1e88e5; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn_alert_up.clicked.connect(self.move_alert_up)

        btn_alert_down = QPushButton("▼ Mover P/ Baixo")
        btn_alert_down.setStyleSheet("background-color: #2e3a4e; color: #64b5f6; border: 1px solid #1e88e5; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn_alert_down.clicked.connect(self.move_alert_down)

        btn_edit_alert = QPushButton("✏️ Editar Obs")
        btn_edit_alert.setStyleSheet("background-color: #333322; color: #ffdd88; border: 1px solid #555522; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn_edit_alert.clicked.connect(self.edit_selected_alert)

        btn_remove_alert = QPushButton("❌ Remover")
        btn_remove_alert.setStyleSheet("background-color: #3a2222; color: #ff8888; border: 1px solid #552222; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn_remove_alert.clicked.connect(self.remove_selected_alert)

        alert_btns_layout.addWidget(btn_alert_up)
        alert_btns_layout.addWidget(btn_alert_down)
        alert_btns_layout.addWidget(btn_edit_alert)
        alert_btns_layout.addWidget(btn_remove_alert)
        alert_layout.addLayout(alert_btns_layout)

        self.tab_widget.addTab(self.alert_tab, "⚠️ Alertas")

        right_layout.addWidget(self.tab_widget)
        splitter.addWidget(right_widget)

        # Proporção inicial 57% esquerda, 43% direita
        splitter.setSizes([570, 430])
        main_layout.addWidget(splitter)

    def load_data(self):
        """Recarrega os dados do histórico, favoritos e alertas."""
        self.render_history()
        self.render_favorites()
        self.render_alerts()

    def render_history(self):
        """Renderiza os cards de histórico no painel esquerdo."""
        while self.history_container_layout.count() > 1:
            child = self.history_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        filter_text = self.search_input.text().strip().lower()
        items = history_manager.get_history()

        for item in items:
            hostname = item.get("hostname", "")
            prefix = item.get("prefix", "")
            patrimony = item.get("patrimony", "")
            timestamp = item.get("timestamp", "")
            active_user = item.get("active_user", "")

            if filter_text and not (filter_text in hostname.lower() or filter_text in patrimony.lower() or filter_text in active_user.lower()):
                continue

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #2b2b2b;
                    border: 1px solid #3d3d3d;
                    border-radius: 6px;
                }
                QFrame:hover {
                    border-color: #207bc1;
                    background-color: #323232;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(6, 4, 6, 4)
            card_layout.setSpacing(3)

            if active_user:
                if "Múltiplos" in active_user:
                    user_str = f"\n⚠️ 👤 {active_user}"
                else:
                    user_str = f"\n👤 Usuário: {active_user}"
            else:
                user_str = ""

            btn_host = QPushButton(f"{hostname}\n({timestamp}){user_str}")
            btn_host.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e1e;
                    color: #207bc1;
                    font-weight: bold;
                    font-size: 13px;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    padding: 6px 10px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #242424;
                    color: #389bed;
                }
            """)
            btn_host.clicked.connect(lambda checked, p=prefix, pat=patrimony: self.select_item(p, pat))
            card_layout.addWidget(btn_host, 1)

            # Botão Lápis Editar Usuário ✏️
            btn_edit_user = QPushButton("✏️")
            btn_edit_user.setToolTip("Editar / Definir Usuário Ativo")
            btn_edit_user.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    font-size: 15px;
                    border: none;
                    min-width: 26px;
                    max-width: 26px;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: #333344;
                    border-radius: 4px;
                }
            """)
            btn_edit_user.clicked.connect(lambda checked, h=hostname, u=active_user: self.prompt_edit_user(h, u))
            card_layout.addWidget(btn_edit_user)

            # Botão Favorito ⭐
            is_fav = history_manager.is_favorite(hostname)
            btn_star = QPushButton("⭐" if is_fav else "☆")
            btn_star.setToolTip("Adicionar/Remover Favorito")
            btn_star.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    font-size: 17px;
                    color: {'#ffca28' if is_fav else '#888888'};
                    border: none;
                    min-width: 26px;
                    max-width: 26px;
                    padding: 0px;
                    margin: 0px;
                }}
                QPushButton:hover {{
                    color: #ffe082;
                }}
            """)
            btn_star.clicked.connect(lambda checked, h=hostname: self.toggle_fav(h))
            card_layout.addWidget(btn_star)

            # Botão Alerta ⚠️
            has_alert = history_manager.get_alert(hostname) is not None
            btn_alert = QPushButton("⚠️" if has_alert else "⚠")
            btn_alert.setToolTip("Adicionar/Editar Alerta")
            btn_alert.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    font-size: 17px;
                    color: {'#ff9800' if has_alert else '#777777'};
                    border: none;
                    min-width: 26px;
                    max-width: 26px;
                    padding: 0px;
                    margin: 0px;
                }}
                QPushButton:hover {{
                    color: #ffb74d;
                }}
            """)
            btn_alert.clicked.connect(lambda checked, h=hostname: self.prompt_alert(h))
            card_layout.addWidget(btn_alert)

            # Botão Lixeira 🗑️
            btn_trash = QPushButton("🗑️")
            btn_trash.setToolTip("Excluir do Histórico")
            btn_trash.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    font-size: 15px;
                    border: none;
                    min-width: 26px;
                    max-width: 26px;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: #442222;
                    border-radius: 4px;
                }
            """)
            btn_trash.clicked.connect(lambda checked, h=hostname: self.delete_history(h))
            card_layout.addWidget(btn_trash)

            # Inserir antes do stretch
            self.history_container_layout.insertWidget(self.history_container_layout.count() - 1, card)

    def render_favorites(self):
        """Renderiza a lista de favoritos exibindo o usuário ativo ao lado do patrimônio."""
        self.fav_list.clear()
        favorites = history_manager.get_favorites()
        for hostname in favorites:
            active_user = history_manager.get_active_user(hostname)
            if active_user and active_user != "Usuário não encontrado":
                user_label = f"  |  👤 {active_user}"
            else:
                user_label = "  |  👤 (Clique em ✏️ Editar Usuário para definir)"
            item = QListWidgetItem(f"⭐  {hostname}{user_label}")
            item.setData(Qt.ItemDataRole.UserRole, hostname)
            self.fav_list.addItem(item)

    def render_alerts(self):
        """Renderiza a lista de alertas com observações."""
        self.alert_list.clear()
        alerts = history_manager.get_alerts()
        for alert_obj in alerts:
            if isinstance(alert_obj, dict):
                hostname = alert_obj.get("hostname", "")
                note = alert_obj.get("note", "Sem observação")
                item = QListWidgetItem(f"⚠️  {hostname}  ➔  [{note}]")
                item.setData(Qt.ItemDataRole.UserRole, hostname)
                self.alert_list.addItem(item)

    def filter_history(self):
        self.render_history()

    def select_item(self, prefix: str, patrimony: str):
        """Seleciona o item e passa para a janela principal."""
        self.item_selected.emit(prefix, patrimony)
        self.accept()

    def toggle_fav(self, hostname: str):
        history_manager.toggle_favorite(hostname)
        self.render_history()
        self.render_favorites()

    def prompt_edit_user(self, hostname: str, current_user: str):
        text, ok = QInputDialog.getText(
            self,
            f"Editar Usuário Ativo - {hostname}",
            f"Informe ou corrija o nome do usuário ativo para {hostname}:",
            QLineEdit.EchoMode.Normal,
            current_user if current_user != "Usuário não encontrado" else ""
        )
        if ok and text.strip():
            new_user = text.strip()
            history_manager.update_active_user(hostname, new_user)
            self.load_data()
            if self.parent() and hasattr(self.parent(), 'update_hostname'):
                self.parent().update_hostname()

    def prompt_alert(self, hostname: str):
        existing = history_manager.get_alert(hostname)
        default_text = existing.get("note", "") if existing else "Não foi possivel realizar"

        options = [
            "Não foi possivel realizar",
            "Computador não faz acesso remoto",
            "Equipamento offline / Desligado",
            "Erro de permissão / Credencial"
        ]

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Observação de Alerta - {hostname}")
        dlg.resize(400, 220)
        dlg.setStyleSheet("QDialog { background-color: #2a2a2a; color: white; } QLabel { color: white; font-weight: bold; } QPushButton { background-color: #3a3a3a; color: white; border-radius: 4px; padding: 6px; margin: 2px; } QPushButton:hover { background-color: #207bc1; } QLineEdit { background-color: #1e1e1e; border: 1px solid #444; color: white; padding: 6px; }")

        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Escolha uma sugestão ou digite uma observação:"))

        line_edit = QLineEdit(default_text)

        for opt in options:
            btn_opt = QPushButton(opt)
            btn_opt.clicked.connect(lambda checked, text=opt: line_edit.setText(text))
            layout.addWidget(btn_opt)

        layout.addWidget(line_edit)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Salvar Alerta")
        btn_save.setStyleSheet("background-color: #207bc1;")
        btn_cancel = QPushButton("Cancelar")

        btn_save.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)

        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            note = line_edit.text().strip()
            if note:
                history_manager.set_alert(hostname, note)
            else:
                history_manager.remove_alert(hostname)
            self.render_history()
            self.render_alerts()

    def delete_history(self, hostname: str):
        history_manager.delete_entry(hostname)
        self.load_data()

    # -------------------------------------------------------------
    # REORDENAÇÃO DE FAVORITOS E ALERTAS VIA SETAS (▲/▼)
    # -------------------------------------------------------------
    def move_favorite_up(self):
        row = self.fav_list.currentRow()
        if row > 0:
            item = self.fav_list.takeItem(row)
            self.fav_list.insertItem(row - 1, item)
            self.fav_list.setCurrentRow(row - 1)
            self.save_favorites_order()

    def move_favorite_down(self):
        row = self.fav_list.currentRow()
        if row >= 0 and row < self.fav_list.count() - 1:
            item = self.fav_list.takeItem(row)
            self.fav_list.insertItem(row + 1, item)
            self.fav_list.setCurrentRow(row + 1)
            self.save_favorites_order()

    def save_favorites_order(self):
        new_order = []
        for i in range(self.fav_list.count()):
            item = self.fav_list.item(i)
            hostname = item.data(Qt.ItemDataRole.UserRole)
            if hostname:
                new_order.append(hostname)
        history_manager.reorder_favorites(new_order)

    def move_alert_up(self):
        row = self.alert_list.currentRow()
        if row > 0:
            item = self.alert_list.takeItem(row)
            self.alert_list.insertItem(row - 1, item)
            self.alert_list.setCurrentRow(row - 1)
            self.save_alerts_order()

    def move_alert_down(self):
        row = self.alert_list.currentRow()
        if row >= 0 and row < self.alert_list.count() - 1:
            item = self.alert_list.takeItem(row)
            self.alert_list.insertItem(row + 1, item)
            self.alert_list.setCurrentRow(row + 1)
            self.save_alerts_order()

    def save_alerts_order(self):
        current_alerts = history_manager.get_alerts()
        alerts_by_host = {a.get("hostname"): a for a in current_alerts if isinstance(a, dict)}

        new_order = []
        for i in range(self.alert_list.count()):
            item = self.alert_list.item(i)
            hostname = item.data(Qt.ItemDataRole.UserRole)
            if hostname and hostname in alerts_by_host:
                new_order.append(alerts_by_host[hostname])

        history_manager.reorder_alerts(new_order)

    def remove_selected_favorite(self):
        current_item = self.fav_list.currentItem()
        if current_item:
            hostname = current_item.data(Qt.ItemDataRole.UserRole)
            if hostname:
                history_manager.toggle_favorite(hostname)
                self.load_data()

    def edit_selected_favorite_user(self):
        current_item = self.fav_list.currentItem()
        if current_item:
            hostname = current_item.data(Qt.ItemDataRole.UserRole)
            if hostname:
                existing_user = history_manager.get_active_user(hostname)
                self.prompt_edit_user(hostname, existing_user)
                self.render_favorites()

    def edit_selected_alert(self):
        current_item = self.alert_list.currentItem()
        if current_item:
            hostname = current_item.data(Qt.ItemDataRole.UserRole)
            if hostname:
                self.prompt_alert(hostname)

    def remove_selected_alert(self):
        current_item = self.alert_list.currentItem()
        if current_item:
            hostname = current_item.data(Qt.ItemDataRole.UserRole)
            if hostname:
                history_manager.remove_alert(hostname)
                self.load_data()

    def on_fav_item_double_clicked(self, item):
        hostname = item.data(Qt.ItemDataRole.UserRole)
        if hostname:
            parts = hostname.split('-')
            if len(parts) >= 3:
                prefix = f"{parts[0]}-{parts[1]}"
                patrimony = parts[-1]
                self.select_item(prefix, patrimony)

    def on_alert_item_double_clicked(self, item):
        hostname = item.data(Qt.ItemDataRole.UserRole)
        if hostname:
            parts = hostname.split('-')
            if len(parts) >= 3:
                prefix = f"{parts[0]}-{parts[1]}"
                patrimony = parts[-1]
                self.select_item(prefix, patrimony)
