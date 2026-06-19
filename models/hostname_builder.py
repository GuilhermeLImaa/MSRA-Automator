class HostnameBuilder:
    @staticmethod
    def build(equipment_type: str, patrimony: str) -> str:
        """
        Constrói o hostname a partir do tipo e do patrimônio.
        
        Args:
            equipment_type (str): O prefixo do equipamento (ex: HUB-WK, HUB-MD, HUB-NT).
            patrimony (str): O número do patrimônio (ex: 123456).
            
        Returns:
            str: O hostname formatado com hífen (ex: HUB-WK-123456).
        """
        if not equipment_type or not patrimony:
            return ""
        
        return f"{equipment_type}-{patrimony.strip()}"
