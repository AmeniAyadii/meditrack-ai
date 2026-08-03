# meditrack-ai/utils/validators.py

from typing import List, Dict, Any, Optional
from datetime import datetime
import re

def validate_measure(measure: Dict[str, Any]) -> List[str]:
    """
    Valider une mesure individuelle
    
    Args:
        measure: Mesure à valider
    
    Returns:
        Liste des erreurs
    """
    errors = []
    
    # Vérifier les champs obligatoires
    required_fields = ['date', 'systolic', 'diastolic']
    for field in required_fields:
        if field not in measure:
            errors.append(f"Champ manquant: {field}")
    
    # Vérifier les valeurs
    systolic = measure.get('systolic')
    if systolic is not None:
        if not isinstance(systolic, (int, float)) or not (50 <= systolic <= 250):
            errors.append(f"Systolique invalide: {systolic}")
    
    diastolic = measure.get('diastolic')
    if diastolic is not None:
        if not isinstance(diastolic, (int, float)) or not (30 <= diastolic <= 160):
            errors.append(f"Diastolique invalide: {diastolic}")
    
    # Vérifier la cohérence
    if systolic is not None and diastolic is not None:
        if systolic <= diastolic:
            errors.append("Systolique doit être > Diastolique")
    
    # Vérifier la date
    date = measure.get('date')
    if date:
        try:
            datetime.fromisoformat(date)
        except (ValueError, TypeError):
            errors.append(f"Date invalide: {date}")
    
    # Vérifier le pouls
    heart_rate = measure.get('heart_rate')
    if heart_rate is not None:
        if not isinstance(heart_rate, (int, float)) or not (20 <= heart_rate <= 220):
            errors.append(f"Pouls invalide: {heart_rate}")
    
    return errors

def validate_measures(measures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Valider une liste de mesures
    
    Args:
        measures: Liste des mesures
    
    Returns:
        Liste des erreurs par mesure
    """
    errors_by_measure = []
    
    for idx, measure in enumerate(measures):
        errors = validate_measure(measure)
        if errors:
            errors_by_measure.append({
                "index": idx,
                "errors": errors
            })
    
    return errors_by_measure

def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoyer les données d'entrée
    
    Args:
        data: Données à nettoyer
    
    Returns:
        Données nettoyées
    """
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Supprimer les espaces en trop
            sanitized[key] = ' '.join(value.split())
        elif isinstance(value, dict):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_input(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized

def validate_email(email: str) -> bool:
    """
    Valider un email
    
    Args:
        email: Email à valider
    
    Returns:
        True si l'email est valide
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """
    Valider un numéro de téléphone
    
    Args:
        phone: Numéro à valider
    
    Returns:
        True si le numéro est valide
    """
    # Accepter différents formats
    patterns = [
        r'^\+?[0-9]{10,15}$',  # International
        r'^0[0-9]{9}$',        # Français
        r'^[0-9]{10}$',        # Simple
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    
    return False