import logging
import os
from pathlib import Path

class MSRALogger:
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "msra.log"
        
        self.logger = logging.getLogger("MSRA")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s | Tipo: %(equipment_type)s | Patrimônio: %(patrimony)s | Hostname: %(hostname)s | Resultado: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            fh = logging.FileHandler(self.log_file, encoding='utf-8')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def log_execution(self, equipment_type: str, patrimony: str, hostname: str, result: str):
        """
        Registra a execução com as informações específicas.
        """
        extra_data = {
            'equipment_type': equipment_type,
            'patrimony': patrimony,
            'hostname': hostname
        }
        self.logger.info(result, extra=extra_data)

# Instância global
msra_logger = MSRALogger()
