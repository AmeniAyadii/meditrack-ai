# meditrack-ai/models/schemas.py

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import re

# ============================================
# ENUMS
# ============================================

class SeverityLevel(str, Enum):
    """Niveau de sévérité"""
    NORMAL = "normal"
    WARNING = "warning"
    DANGER = "danger"

class Category(str, Enum):
    """Catégorie de tension"""
    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRISIS = "crisis"

class Stability(str, Enum):
    """Stabilité de la tension"""
    STABLE = "stable"
    INCREASING = "increasing"
    DECREASING = "decreasing"
    VOLATILE = "volatile"

# ============================================
# SCHEMAS D'ENTRÉE
# ============================================

class SingleMeasure(BaseModel):
    """Mesure individuelle de tension"""
    systolic: int = Field(..., ge=50, le=250, description="Pression systolique en mmHg")
    diastolic: int = Field(..., ge=30, le=160, description="Pression diastolique en mmHg")
    heart_rate: Optional[int] = Field(None, ge=20, le=220, description="Fréquence cardiaque en bpm")
    measure_date: Optional[str] = Field(None, description="Date de la mesure (ISO format)")
    user_id: Optional[int] = Field(None, description="ID de l'utilisateur")
    notes: Optional[str] = Field(None, max_length=500, description="Notes supplémentaires")
    
    @field_validator('measure_date')
    @classmethod
    def validate_measure_date(cls, v):
        """Valider le format de la date"""
        if v:
            try:
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError("Format de date invalide. Utilisez ISO format (YYYY-MM-DDTHH:MM:SS)")
        return v
    
    @model_validator(mode='after')
    def validate_tension(self):
        """Valider la cohérence tension systolique/diastolique"""
        if self.systolic <= self.diastolic:
            raise ValueError("La pression systolique doit être supérieure à la diastolique")
        return self

class TrendAnalysis(BaseModel):
    """Requête d'analyse de tendance"""
    measures: List[Dict[str, Any]] = Field(..., min_length=3, description="Liste des mesures")
    user_id: Optional[int] = Field(None, description="ID de l'utilisateur")
    
    @field_validator('measures')
    @classmethod
    def validate_measures(cls, v):
        """Valider chaque mesure"""
        required_fields = ['date', 'systolic', 'diastolic']
        for idx, measure in enumerate(v):
            # Vérifier les champs requis
            for field in required_fields:
                if field not in measure:
                    raise ValueError(f"Measure {idx}: champ '{field}' manquant")
            
            # Valider les valeurs
            systolic = measure.get('systolic')
            diastolic = measure.get('diastolic')
            
            if not (50 <= systolic <= 250):
                raise ValueError(f"Measure {idx}: systolique invalide ({systolic})")
            if not (30 <= diastolic <= 160):
                raise ValueError(f"Measure {idx}: diastolique invalide ({diastolic})")
            if systolic <= diastolic:
                raise ValueError(f"Measure {idx}: systolique doit être > diastolique")
            
            # Valider la date
            try:
                datetime.fromisoformat(measure.get('date'))
            except (ValueError, TypeError):
                raise ValueError(f"Measure {idx}: date invalide")
        
        return v

# ============================================
# SCHEMAS DE RÉPONSE
# ============================================

class SingleAnalysisResponse(BaseModel):
    """Réponse pour l'analyse d'une mesure individuelle"""
    summary: str = Field(..., description="Résumé de l'analyse")
    recommendation: str = Field(..., description="Recommandations")
    severity_level: SeverityLevel = Field(..., description="Niveau de sévérité")
    details: Dict[str, Any] = Field(..., description="Détails de l'analyse")
    timestamp: str = Field(..., description="Horodatage de l'analyse")

class TrendAnalysisResponse(BaseModel):
    """Réponse pour l'analyse des tendances"""
    summary: str = Field(..., description="Résumé de l'analyse")
    recommendation: str = Field(..., description="Recommandations")
    severity_level: SeverityLevel = Field(..., description="Niveau de sévérité")
    details: Dict[str, Any] = Field(..., description="Détails de l'analyse")
    
    # Champs optionnels pour plus de détails
    statistics: Optional[Dict[str, Any]] = Field(None, description="Statistiques des mesures")
    predictions: Optional[Dict[str, Any]] = Field(None, description="Prédictions futures")

class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    error: str = Field(..., description="Code d'erreur")
    message: str = Field(..., description="Message d'erreur")
    details: Optional[Dict[str, Any]] = Field(None, description="Détails supplémentaires")
    timestamp: str = Field(..., description="Horodatage de l'erreur")

class HealthResponse(BaseModel):
    """Réponse de santé du service"""
    status: str = Field(..., description="Statut du service")
    version: str = Field(..., description="Version de l'API")
    uptime: float = Field(..., description="Temps de fonctionnement en secondes")
    timestamp: str = Field(..., description="Horodatage")

# ============================================
# REFERENCE VALUES
# ============================================

class ReferenceValues(BaseModel):
    """Valeurs de référence pour la tension artérielle"""
    normal: Dict[str, Any] = {
        "systolic_min": 90,
        "systolic_max": 140,
        "diastolic_min": 60,
        "diastolic_max": 90,
        "heart_rate_min": 60,
        "heart_rate_max": 100,
        "label": "Normale"
    }
    elevated: Dict[str, Any] = {
        "systolic_min": 140,
        "systolic_max": 160,
        "diastolic_min": 90,
        "diastolic_max": 100,
        "label": "Élevée"
    }
    hypertension_stage1: Dict[str, Any] = {
        "systolic_min": 160,
        "systolic_max": 180,
        "diastolic_min": 100,
        "diastolic_max": 110,
        "label": "Hypertension stade 1"
    }
    hypertension_stage2: Dict[str, Any] = {
        "systolic_min": 180,
        "systolic_max": 250,
        "diastolic_min": 110,
        "diastolic_max": 160,
        "label": "Hypertension stade 2"
    }
    hypotension: Dict[str, Any] = {
        "systolic_min": 0,
        "systolic_max": 90,
        "diastolic_min": 0,
        "diastolic_max": 60,
        "label": "Hypotension"
    }