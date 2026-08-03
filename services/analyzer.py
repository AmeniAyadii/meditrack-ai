# meditrack-ai/services/analyzer.py

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from models.schemas import (
    SingleMeasure, SingleAnalysisResponse, TrendAnalysisResponse,
    SeverityLevel, Category, Stability
)
from models.tension import (
    TensionClassifier, TensionStatistics, 
    TensionPredictor, TensionTrendAnalyzer
)
from utils.logger import logger
from config import settings
import json
import os


def convert_numpy_types(obj: Any) -> Any:
    """Convertir les types numpy en types Python natifs"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (pd.Series, pd.DataFrame)):
        return obj.to_dict()
    else:
        return obj


class TensionAnalyzer:
    """Service principal d'analyse de tension"""
    
    def __init__(self):
        """Initialiser l'analyseur"""
        self.classifier = TensionClassifier()
        self.stats_calculator = TensionStatistics()
        self.predictor = TensionPredictor()
        self.trend_analyzer = TensionTrendAnalyzer()
        self.reference_values = self._load_reference_values()
        logger.info("Analyseur de tension initialisé")
    
    def _load_reference_values(self) -> Dict[str, Any]:
        """Charger les valeurs de référence depuis un fichier"""
        default_values = {
            "normal": {
                "systolic_min": 90, "systolic_max": 140,
                "diastolic_min": 60, "diastolic_max": 90,
                "label": "Normale"
            },
            "elevated": {
                "systolic_min": 140, "systolic_max": 160,
                "diastolic_min": 90, "diastolic_max": 100,
                "label": "Élevée"
            },
            "hypertension_stage1": {
                "systolic_min": 160, "systolic_max": 180,
                "diastolic_min": 100, "diastolic_max": 110,
                "label": "Hypertension stade 1"
            },
            "hypertension_stage2": {
                "systolic_min": 180, "systolic_max": 250,
                "diastolic_min": 110, "diastolic_max": 160,
                "label": "Hypertension stade 2"
            },
            "hypotension": {
                "systolic_min": 0, "systolic_max": 90,
                "diastolic_min": 0, "diastolic_max": 60,
                "label": "Hypotension"
            }
        }
        
        try:
            if os.path.exists(settings.REFERENCE_VALUES_PATH):
                with open(settings.REFERENCE_VALUES_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                os.makedirs(os.path.dirname(settings.REFERENCE_VALUES_PATH), exist_ok=True)
                with open(settings.REFERENCE_VALUES_PATH, 'w', encoding='utf-8') as f:
                    json.dump(default_values, f, indent=2, ensure_ascii=False)
                return default_values
        except Exception as e:
            logger.error(f"Erreur lors du chargement des valeurs de référence: {e}")
            return default_values
    
    def analyze_single_measure(self, measure: SingleMeasure) -> SingleAnalysisResponse:
        """Analyser une mesure individuelle"""
        logger.info(f"Analyse d'une mesure: {measure.systolic}/{measure.diastolic}")
        
        category = self.classifier.classify(measure.systolic, measure.diastolic)
        severity = self.classifier.get_severity(category)
        
        summary, recommendation = self._generate_single_analysis(
            measure.systolic, 
            measure.diastolic, 
            measure.heart_rate,
            category
        )
        
        details = {
            "category": category.value,
            "category_label": self._get_category_label(category),
            "systolic": measure.systolic,
            "diastolic": measure.diastolic,
            "heart_rate": measure.heart_rate,
            "severity": severity.value,
            "color": self.classifier.get_color(category),
            "icon": self.classifier.get_icon(category),
            "measure_date": measure.measure_date or datetime.now().isoformat(),
        }
        
        if measure.heart_rate:
            heart_rate_advice = self._analyze_heart_rate(measure.heart_rate)
            if heart_rate_advice:
                details["heart_rate_advice"] = heart_rate_advice
                recommendation += " " + heart_rate_advice
        
        return SingleAnalysisResponse(
            summary=summary,
            recommendation=recommendation,
            severity_level=severity,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def analyze_trends(self, measures: List[Dict[str, Any]]) -> TrendAnalysisResponse:
        """Analyser les tendances à partir d'une liste de mesures"""
        logger.info(f"Analyse des tendances: {len(measures)} mesures")
        
        if len(measures) < 3:
            return TrendAnalysisResponse(
                summary="📊 Pas assez de données pour une analyse de tendance",
                recommendation="Continuez à enregistrer vos mesures régulièrement. L'analyse nécessite au moins 3 mesures.",
                severity_level=SeverityLevel.NORMAL,
                details={"message": "Insufficient data", "minimum_required": 3}
            )
        
        try:
            df = pd.DataFrame(measures)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['day_index'] = (df['date'] - df['date'].min()).dt.days
            
            stats = self.stats_calculator.compute_stats(measures)
            stats = convert_numpy_types(stats)
            
            df['category'] = df.apply(
                lambda row: self.classifier.classify(row['systolic'], row['diastolic']).value,
                axis=1
            )
            
            trend_analysis = self.trend_analyzer.analyze_trend(measures)
            trend_analysis = convert_numpy_types(trend_analysis)
            
            outliers = self.stats_calculator.detect_outliers(measures)
            outliers = [int(o) if isinstance(o, np.integer) else o for o in outliers]
            
            predictions = self.predictor.predict_future(measures)
            predictions = convert_numpy_types(predictions)
            
            summary, recommendation, severity = self._generate_trend_analysis(
                stats, trend_analysis, outliers, predictions
            )
            
            details = {
                "measure_count": len(measures),
                "period_days": int((df['date'].max() - df['date'].min()).days) + 1,
                "avg_systolic": float(round(stats['systolic']['mean'], 1)),
                "avg_diastolic": float(round(stats['diastolic']['mean'], 1)),
                "min_systolic": float(round(stats['systolic']['min'], 1)),
                "max_systolic": float(round(stats['systolic']['max'], 1)),
                "min_diastolic": float(round(stats['diastolic']['min'], 1)),
                "max_diastolic": float(round(stats['diastolic']['max'], 1)),
                "categories_distribution": stats.get('categories_distribution', {}),
                "outliers_count": len(outliers),
                "stability": trend_analysis.get('stability', Stability.STABLE).value if trend_analysis.get('available') else "unknown",
                "trend_systolic": float(trend_analysis.get('trends', {}).get('systolic', {}).get('trend', 0)),
                "trend_diastolic": float(trend_analysis.get('trends', {}).get('diastolic', {}).get('trend', 0)),
            }
            
            statistics = {
                "total_measures": len(measures),
                "average_systolic": float(round(stats['systolic']['mean'], 1)),
                "average_diastolic": float(round(stats['diastolic']['mean'], 1)),
                "min_systolic": float(round(stats['systolic']['min'], 1)),
                "max_systolic": float(round(stats['systolic']['max'], 1)),
            }
            
            if 'heart_rate' in stats:
                statistics['average_heart_rate'] = float(round(stats['heart_rate']['mean'], 1))
            
            result = TrendAnalysisResponse(
                summary=summary,
                recommendation=recommendation,
                severity_level=severity,
                details=details,
                statistics=statistics,
                predictions=predictions if predictions.get('available') else None
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des tendances: {str(e)}")
            return TrendAnalysisResponse(
                summary="❌ Erreur lors de l'analyse des tendances",
                recommendation="Veuillez réessayer ultérieurement. Si le problème persiste, contactez le support.",
                severity_level=SeverityLevel.NORMAL,
                details={"error": str(e)}
            )
    
    def _generate_single_analysis(self, systolic: int, diastolic: int, 
                                  heart_rate: Optional[int], 
                                  category: Category) -> Tuple[str, str]:
        """Générer le résumé et les recommandations pour une mesure unique"""
        
        category_label = self._get_category_label(category)
        summary = f"{self.classifier.get_icon(category)} {category_label}: {systolic}/{diastolic} mmHg"
        
        recommendations_map = {
            Category.NORMAL: (
                "Excellent ! Votre tension est dans les limites normales. "
                "Continuez à surveiller régulièrement pour maintenir une bonne santé cardiovasculaire."
            ),
            Category.LOW: (
                "⚠️ Votre tension est basse. Assurez-vous de bien vous hydrater, "
                "mangez des aliments salés si nécessaire. Consultez un médecin si vous avez des vertiges "
                "ou des étourdissements."
            ),
            Category.HIGH: (
                "⚠️ Votre tension est élevée. Surveillez votre alimentation, réduisez le sel, "
                "pratiquez une activité physique régulière. Consultez un médecin pour un bilan "
                "cardiovasculaire si cela persiste."
            ),
            Category.CRISIS: (
                "🚨 URGENCE MÉDICALE ! Votre tension est dangereusement élevée. "
                "Appelez immédiatement le 15 (SAMU) ou rendez-vous aux urgences. "
                "Ne conduisez pas et évitez tout effort."
            )
        }
        
        recommendation = recommendations_map.get(category, "")
        
        if category == Category.HIGH:
            if systolic > 160:
                recommendation += " Votre systolique est particulièrement élevée, consultez rapidement."
            if diastolic > 100:
                recommendation += " Votre diastolique est préoccupante, prenez rendez-vous avec votre médecin."
        
        return summary, recommendation
    
    def _generate_trend_analysis(self, stats: Dict[str, Any], 
                                 trend_analysis: Dict[str, Any],
                                 outliers: List[int],
                                 predictions: Dict[str, Any]) -> Tuple[str, str, SeverityLevel]:
        """Générer le résumé et les recommandations pour l'analyse des tendances"""
        
        avg_systolic = stats['systolic']['mean']
        avg_diastolic = stats['diastolic']['mean']
        count = stats['count']
        
        avg_category = self.classifier.classify(int(avg_systolic), int(avg_diastolic))
        severity = self.classifier.get_severity(avg_category)
        
        summary = f"📊 Analyse de {count} mesures récentes\n"
        summary += f"Moyenne: {avg_systolic:.0f}/{avg_diastolic:.0f} mmHg\n"
        summary += f"Min/Max: {stats['systolic']['min']:.0f}/{stats['systolic']['max']:.0f} mmHg"
        
        if trend_analysis.get('available'):
            stability = trend_analysis.get('stability')
            if stability == Stability.STABLE:
                summary += "\n➡️ Tension stable dans le temps"
            elif stability == Stability.INCREASING:
                trend = trend_analysis.get('trends', {}).get('systolic', {}).get('trend', 0)
                summary += f"\n📈 Tendance à la hausse: +{trend:.1f} mmHg/jour"
            elif stability == Stability.DECREASING:
                trend = trend_analysis.get('trends', {}).get('systolic', {}).get('trend', 0)
                summary += f"\n📉 Tendance à la baisse: {trend:.1f} mmHg/jour"
        
        if outliers:
            summary += f"\n⚠️ {len(outliers)} mesures anormales détectées"
        
        if predictions.get('available'):
            pred_sys = predictions.get('predictions', {}).get('systolic', {}).get('future_values', [])
            if pred_sys:
                diast_values = predictions.get('predictions', {}).get('diastolic', {}).get('future_values', [0])
                summary += f"\n🔮 Prédiction 7 jours: {pred_sys[-1]:.0f}/{diast_values[-1]:.0f} mmHg"
        
        recommendation = ""
        
        if severity == SeverityLevel.DANGER:
            recommendation = (
                "🚨 URGENCE : Votre tension moyenne est très élevée. "
                "Consultez un médecin immédiatement pour un bilan cardiovasculaire complet."
            )
        elif severity == SeverityLevel.WARNING:
            if avg_systolic > 140:
                recommendation = (
                    "⚠️ Votre tension est élevée. Adoptez un mode de vie sain : "
                    "alimentation équilibrée (moins de sel), activité physique régulière, "
                    "gestion du stress. Consultez votre médecin pour un suivi."
                )
            elif avg_systolic < 90:
                recommendation = (
                    "⚠️ Votre tension est basse. Assurez-vous de bien vous hydrater, "
                    "surveillez les vertiges. Consultez un médecin si les symptômes persistent."
                )
            else:
                recommendation = (
                    "Surveillez régulièrement votre tension. Une tendance à la hausse "
                    "peut nécessiter une consultation médicale."
                )
        else:
            recommendation = (
                "✅ Bonne santé cardiovasculaire ! Continuez à surveiller votre tension "
                "régulièrement pour maintenir cet équilibre."
            )
        
        if trend_analysis.get('available') and trend_analysis.get('stability') == Stability.INCREASING:
            recommendation += " Puisque votre tension a tendance à augmenter, il est conseillé de consulter pour un bilan préventif."
        
        return summary, recommendation, severity
    
    def _get_category_label(self, category: Category) -> str:
        """Obtenir le libellé de la catégorie"""
        labels = {
            Category.NORMAL: "Tension normale",
            Category.LOW: "Hypotension",
            Category.HIGH: "Hypertension",
            Category.CRISIS: "CRISE HYPERTENSIVE"
        }
        return labels.get(category, "Inconnue")
    
    def _analyze_heart_rate(self, heart_rate: int) -> Optional[str]:
        """Analyser la fréquence cardiaque"""
        if heart_rate < 60:
            return "Pouls bas (bradycardie). Normal si sportif, sinon consultez un médecin."
        elif heart_rate > 100:
            return "Pouls élevé (tachycardie). Surveillez le stress et la caféine. Consultez si persistant."
        else:
            return None