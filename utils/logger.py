# meditrack-ai/utils/logger.py

import logging
import sys
from datetime import datetime
from pathlib import Path
from config import settings
import json

class JsonFormatter(logging.Formatter):
    """Formateur de logs en JSON"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Ajouter les exceptions
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Ajouter les attributs personnalisés
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 
                          'filename', 'funcName', 'levelname', 'levelno', 
                          'lineno', 'module', 'msecs', 'message', 'msg', 
                          'name', 'pathname', 'process', 'processName', 
                          'relativeCreated', 'stack_info', 'thread', 'threadName']:
                log_data[key] = value
        
        return json.dumps(log_data)

def setup_logging():
    """Configurer le logging"""
    # Créer le dossier logs si nécessaire
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurer le logger racine
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Supprimer les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler pour la console (JSON)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)
    
    # Handler pour le fichier (JSON)
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    
    # Handler pour la console (Debug - format lisible)
    debug_handler = logging.StreamHandler(sys.stdout)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(debug_handler)
    
    return logger

# Créer un logger pour l'application
logger = setup_logging()

def get_logger(name: str) -> logging.Logger:
    """Obtenir un logger nommé"""
    return logging.getLogger(name)