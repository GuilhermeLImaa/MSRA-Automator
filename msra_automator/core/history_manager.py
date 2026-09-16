import os
import json
from datetime import datetime
from pathlib import Path

class HistoryManager:
    """Gerencia a persistência do histórico de acessos, favoritos e alertas."""
    
    def __init__(self, filepath: str = None):
        if filepath is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            self.filepath = log_dir / "history_data.json"
        else:
            self.filepath = Path(filepath)
            
        self.data = {
            "history": [],
            "favorites": [],
            "alerts": []
        }
        self.load()

    def load(self):
        """Carrega os dados do arquivo JSON."""
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    self.data["history"] = content.get("history", [])
                    self.data["favorites"] = content.get("favorites", [])
                    self.data["alerts"] = content.get("alerts", [])
            except Exception as e:
                print(f"Erro ao carregar histórico: {e}")

    def save(self):
        """Salva os dados no arquivo JSON."""
        try:
            self.filepath.parent.mkdir(exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")

    def add_entry(self, prefix: str, patrimony: str, hostname: str):
        """Adiciona uma entrada ao histórico sem limite de quantidade."""
        if not hostname or not patrimony:
            return

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        existing_user = None
        for item in self.data.get("history", []):
            if item.get("hostname") == hostname:
                existing_user = item.get("active_user")
                break

        # Remove entrada idêntica anterior se existir para reposicionar no topo
        self.data["history"] = [
            item for item in self.data["history"] 
            if item.get("hostname") != hostname
        ]
        
        # Adiciona no início da lista (mais recente primeiro)
        new_entry = {
            "prefix": prefix,
            "patrimony": patrimony,
            "hostname": hostname,
            "timestamp": now_str
        }
        if existing_user:
            new_entry["active_user"] = existing_user

        self.data["history"].insert(0, new_entry)
        self.save()

    def update_active_user(self, hostname: str, user_str: str):
        """Atualiza a informação de usuário ativo para um registro no histórico."""
        for item in self.data.get("history", []):
            if item.get("hostname") == hostname:
                item["active_user"] = user_str
                break
        self.save()

    def get_active_user(self, hostname: str) -> str:
        """Retorna o usuário ativo salvo para o hostname."""
        for item in self.data.get("history", []):
            if item.get("hostname") == hostname:
                return item.get("active_user", "")
        return ""

    def get_history(self) -> list:
        """Retorna a lista completa do histórico."""
        return self.data.get("history", [])

    def delete_entry(self, hostname: str):
        """Remove uma entrada do histórico, favoritos e alertas."""
        self.data["history"] = [
            item for item in self.data["history"] 
            if item.get("hostname") != hostname
        ]
        self.data["favorites"] = [
            h for h in self.data["favorites"] 
            if h != hostname
        ]
        self.data["alerts"] = [
            a for a in self.data["alerts"] 
            if isinstance(a, dict) and a.get("hostname") != hostname
        ]
        self.save()

    def is_favorite(self, hostname: str) -> bool:
        """Verifica se um hostname é favorito."""
        return hostname in self.data.get("favorites", [])

    def toggle_favorite(self, hostname: str) -> bool:
        """Alterna o status de favorito de um hostname."""
        if self.is_favorite(hostname):
            self.data["favorites"].remove(hostname)
            is_fav = False
        else:
            self.data["favorites"].append(hostname)
            is_fav = True
        self.save()
        return is_fav

    def get_favorites(self) -> list:
        """Retorna a lista de favoritos mantendo a ordem reordenada."""
        return self.data.get("favorites", [])

    def reorder_favorites(self, new_order: list):
        """Atualiza a ordem dos favoritos após drag and drop."""
        self.data["favorites"] = new_order
        self.save()

    def get_alert(self, hostname: str) -> dict:
        """Retorna o alerta correspondente ao hostname se existir."""
        for item in self.data.get("alerts", []):
            if isinstance(item, dict) and item.get("hostname") == hostname:
                return item
        return None

    def set_alert(self, hostname: str, note: str):
        """Adiciona ou atualiza um alerta com observação personalizada."""
        existing = self.get_alert(hostname)
        if existing:
            existing["note"] = note
            existing["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        else:
            self.data["alerts"].append({
                "hostname": hostname,
                "note": note,
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
            })
        self.save()

    def remove_alert(self, hostname: str):
        """Remove o alerta de um hostname."""
        self.data["alerts"] = [
            a for a in self.data["alerts"] 
            if isinstance(a, dict) and a.get("hostname") != hostname
        ]
        self.save()

    def get_alerts(self) -> list:
        """Retorna a lista de alertas."""
        return self.data.get("alerts", [])

    def reorder_alerts(self, new_order: list):
        """Atualiza a ordem dos alertas após drag and drop."""
        self.data["alerts"] = new_order
        self.save()

    def get_suggestions(self) -> list:
        """Retorna lista de sugestões únicas para o autocompletar."""
        suggestions = set()
        for item in self.data.get("history", []):
            pat = item.get("patrimony")
            host = item.get("hostname")
            if pat:
                suggestions.add(pat)
            if host:
                suggestions.add(host)
        return sorted(list(suggestions))

# Instância global para ser reutilizada
history_manager = HistoryManager()
