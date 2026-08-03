# meditrack-ai/services/symptom_analyzer.py

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import Counter
import math
import json
from utils.logger import logger

class SymptomAnalyzer:
    """Service d'analyse IA des symptômes"""
    
    def __init__(self):
        self.symptom_types = {
            'douleur': ['douleur', 'mal', 'crampe', 'déchirure', 'brûlure'],
            'fatigue': ['fatigue', 'épuisement', 'faiblesse', 'lassitude', 'somnolence'],
            'digestif': ['nausée', 'vomissement', 'diarrhée', 'constipation', 'ballonnement', 'reflux'],
            'respiratoire': ['toux', 'essoufflement', 'expectoration', 'respiration', 'sifflement'],
            'neurologique': ['migraine', 'vertige', 'engourdissement', 'fourmillement', 'tremblement'],
            'cardiaque': ['palpitation', 'tachycardie', 'douleur', 'oppression'],
            'musculaire': ['courbature', 'raideur', 'contracture', 'spasme'],
            'cutané': ['éruption', 'démangeaison', 'rougeur', 'bouton', 'desquamation']
        }
    
    def _clean_value(self, value: Any) -> Any:
        """
        Nettoyer une valeur pour éviter les erreurs JSON
        
        Convertit les NaN, Inf, -Inf en 0 ou valeurs par défaut
        """
        if value is None:
            return 0
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return 0.0
            return value
        if isinstance(value, dict):
            return {k: self._clean_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._clean_value(v) for v in value]
        if isinstance(value, (np.float64, np.float32)):
            if np.isnan(value) or np.isinf(value):
                return 0.0
            return float(value)
        if isinstance(value, (np.int64, np.int32)):
            return int(value)
        if isinstance(value, pd.Series):
            return self._clean_value(value.tolist())
        if isinstance(value, pd.DataFrame):
            return self._clean_value(value.to_dict('records'))
        return value
    
    def _safe_mean(self, values: List[float]) -> float:
        """Calculer la moyenne en ignorant les NaN"""
        if not values:
            return 0.0
        clean_values = [v for v in values if not (math.isnan(v) or math.isinf(v)) if v is not None]
        if not clean_values:
            return 0.0
        return sum(clean_values) / len(clean_values)
    
    def _safe_std(self, values: List[float]) -> float:
        """Calculer l'écart-type en ignorant les NaN"""
        if len(values) < 2:
            return 0.0
        clean_values = [v for v in values if not (math.isnan(v) or math.isinf(v)) if v is not None]
        if len(clean_values) < 2:
            return 0.0
        mean = sum(clean_values) / len(clean_values)
        variance = sum((x - mean) ** 2 for x in clean_values) / len(clean_values)
        return math.sqrt(variance)
    
    def analyze_symptoms(self, symptoms_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyser les symptômes et retourner des insights
        
        Args:
            symptoms_data: Liste des symptômes avec leurs attributs
            
        Returns:
            Dict contenant l'analyse complète
        """
        logger.info(f"Analyse IA de {len(symptoms_data)} symptômes")
        
        if not symptoms_data:
            return self._empty_analysis()
        
        # Convertir en DataFrame avec gestion des erreurs
        try:
            df = pd.DataFrame(symptoms_data)
            
            # Vérifier les colonnes nécessaires
            required_cols = ['date_enregistrement', 'status', 'type', 'niveau']
            for col in required_cols:
                if col not in df.columns:
                    logger.warning(f"Colonne manquante: {col}")
                    df[col] = None
            
            # Convertir les dates
            try:
                df['date'] = pd.to_datetime(df['date_enregistrement'])
            except:
                df['date'] = pd.to_datetime(datetime.now())
            
            df = df.sort_values('date')
            
        except Exception as e:
            logger.error(f"Erreur de conversion DataFrame: {e}")
            return self._empty_analysis()
        
        # Vérifier que le DataFrame n'est pas vide
        if df.empty:
            return self._empty_analysis()
        
        # Analyses avec gestion des erreurs
        result = {
            'summary': self._generate_summary(df),
            'patterns': self._detect_patterns(df),
            'correlations': self._find_correlations(df),
            'predictions': self._predict_evolution(df),
            'recommendations': self._generate_recommendations(df),
            'insights': self._extract_insights(df),
            'severity_trend': self._analyze_severity_trend(df),
        }
        
        # Nettoyer TOUTES les valeurs NaN/Inf
        cleaned_result = self._clean_value(result)
        
        logger.info("✅ Analyse IA terminée avec succès")
        return cleaned_result
    
    def _empty_analysis(self) -> Dict[str, Any]:
        return {
            'summary': "Aucun symptôme enregistré",
            'patterns': {},
            'correlations': {},
            'predictions': {},
            'recommendations': "Commencez à enregistrer vos symptômes pour bénéficier d'une analyse personnalisée.",
            'insights': {},
            'severity_trend': {}
        }
    
    def _generate_summary(self, df: pd.DataFrame) -> str:
        """Générer un résumé de l'état des symptômes"""
        total = len(df)
        
        # Vérifier si la colonne status existe
        if 'status' not in df.columns:
            return f"📊 **Analyse de {total} symptômes**\n\n📝 Enregistrez le statut de vos symptômes pour une analyse plus complète."
        
        active = len(df[df['status'] == 'actif']) if 'status' in df.columns else 0
        resolved = len(df[df['status'] == 'resolu']) if 'status' in df.columns else 0
        evolving = len(df[df['status'] == 'en_amelioration']) if 'status' in df.columns else 0
        worsening = len(df[df['status'] == 'aggravation']) if 'status' in df.columns else 0
        
        # Types les plus fréquents
        if 'type' in df.columns and not df['type'].empty:
            type_counts = df['type'].value_counts()
            top_types = type_counts.head(3).index.tolist() if not type_counts.empty else ['Non défini']
        else:
            top_types = ['Non défini']
        
        # Niveau moyen
        avg_level = df['niveau'].mean() if 'niveau' in df.columns else 0
        if math.isnan(avg_level):
            avg_level = 0
        
        summary = f"""📊 **Analyse de {total} symptômes**

🔵 **Symptômes actifs:** {active}  
🟢 **Résolus:** {resolved}  
🟡 **En amélioration:** {evolving}  
🔴 **En aggravation:** {worsening}

📈 **Niveau moyen:** {avg_level:.1f}/10
🏷️ **Types les plus fréquents:** {', '.join(top_types)}

"""
        
        if avg_level > 6:
            summary += "⚠️ **Attention:** Niveau de sévérité élevé. Il est recommandé de consulter un médecin."
        elif avg_level > 4:
            summary += "📌 **Suivi recommandé:** Continuez à surveiller vos symptômes."
        else:
            summary += "✅ **Bon suivi:** Vos symptômes sont sous contrôle."
        
        return summary
    
    def _detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Détecter des patterns dans l'apparition des symptômes"""
        patterns = {}
        
        if 'type' not in df.columns or df.empty:
            return patterns
        
        # Pattern temporel par type
        for symptom_type in df['type'].unique():
            if symptom_type is None:
                continue
                
            type_data = df[df['type'] == symptom_type]
            if len(type_data) > 1 and 'date' in type_data.columns:
                try:
                    dates = type_data['date'].sort_values()
                    intervals = dates.diff().dt.days.dropna()
                    
                    if not intervals.empty:
                        avg_interval = intervals.mean()
                        if not math.isnan(avg_interval):
                            patterns[str(symptom_type)] = {
                                'frequency': f"Tous les {avg_interval:.1f} jours en moyenne",
                                'count': len(type_data),
                                'trend': self._detect_trend(type_data),
                            }
                except Exception as e:
                    logger.warning(f"Erreur pattern pour {symptom_type}: {e}")
                    continue
        
        return patterns
    
    def _detect_trend(self, data: pd.DataFrame) -> str:
        """Détecter la tendance d'un type de symptôme"""
        if len(data) < 2 or 'niveau' not in data.columns:
            return "stable"
        
        try:
            values = data['niveau'].values
            first_half = self._safe_mean(values[:len(values)//2])
            second_half = self._safe_mean(values[len(values)//2:])
            
            if second_half > first_half * 1.2:
                return "augmentation"
            elif second_half < first_half * 0.8:
                return "diminution"
            else:
                return "stable"
        except:
            return "stable"
    
    def _find_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Trouver des corrélations entre les symptômes"""
        correlations = {}
        
        if 'type' not in df.columns or 'date' not in df.columns or df.empty:
            return correlations
        
        try:
            types = df['type'].dropna().unique()
            if len(types) < 2:
                return correlations
            
            for i, type1 in enumerate(types):
                for type2 in types[i+1:]:
                    if type1 is None or type2 is None:
                        continue
                        
                    dates1 = set(df[df['type'] == type1]['date'].dt.date) if 'date' in df.columns else set()
                    dates2 = set(df[df['type'] == type2]['date'].dt.date) if 'date' in df.columns else set()
                    
                    if dates1 and dates2:
                        co_occurrences = dates1.intersection(dates2)
                        if len(co_occurrences) >= 2:
                            correlations[f"{type1}-{type2}"] = {
                                'co_occurrences': len(co_occurrences),
                                'strength': len(co_occurrences) / min(len(dates1), len(dates2)),
                            }
        except Exception as e:
            logger.warning(f"Erreur corrélation: {e}")
        
        return correlations
    
    def _predict_evolution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Prédire l'évolution des symptômes"""
        predictions = {}
        
        if 'type' not in df.columns or 'status' not in df.columns or df.empty:
            return predictions
        
        try:
            active_types = df[df['status'] == 'actif']['type'].dropna().unique()
            
            for symptom_type in active_types:
                if symptom_type is None:
                    continue
                    
                type_data = df[df['type'] == symptom_type]
                if len(type_data) > 2 and 'niveau' in type_data.columns:
                    try:
                        days = (type_data['date'] - type_data['date'].min()).dt.days.values
                        levels = type_data['niveau'].values
                        
                        if len(days) > 1:
                            from sklearn.linear_model import LinearRegression
                            X = days.reshape(-1, 1)
                            y = levels
                            model = LinearRegression().fit(X, y)
                            
                            trend = float(model.coef_[0])
                            if not math.isnan(trend):
                                predictions[str(symptom_type)] = {
                                    'current_avg': float(self._safe_mean(levels.tolist())),
                                    'trend': trend,
                                    'risk': 'Élevé' if trend > 0.3 else 'Modéré' if trend > 0.1 else 'Faible'
                                }
                    except Exception as e:
                        logger.warning(f"Erreur prédiction pour {symptom_type}: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Erreur prédiction globale: {e}")
        
        return predictions
    
    def _generate_recommendations(self, df: pd.DataFrame) -> str:
        """Générer des recommandations personnalisées"""
        recommendations = []
        
        if df.empty:
            return "Commencez à enregistrer vos symptômes pour bénéficier d'une analyse personnalisée."
        
        try:
            # Analyser les symptômes actifs
            if 'status' in df.columns:
                active = df[df['status'] == 'actif']
                if not active.empty and 'niveau' in active.columns:
                    avg_level = self._safe_mean(active['niveau'].values.tolist())
                    if avg_level > 7:
                        recommendations.append("🚨 **URGENT:** Consultez un médecin rapidement. Vos symptômes actifs sont sévères.")
                    elif avg_level > 5:
                        recommendations.append("⚠️ **Attention:** Surveillez vos symptômes. Consultez si la situation s'aggrave.")
                
                # Recommandations par type
                if 'type' in active.columns:
                    for symptom_type in active['type'].dropna().unique():
                        if symptom_type:
                            type_data = active[active['type'] == symptom_type]
                            avg_level = self._safe_mean(type_data['niveau'].values.tolist()) if 'niveau' in type_data.columns else 0
                            recommendations.append(self._get_type_recommendation(str(symptom_type), avg_level))
            
            # Recommandations générales
            if len(recommendations) < 3:
                recommendations.append("📋 Continuez à suivre vos symptômes quotidiennement.")
                recommendations.append("💡 Gardez une alimentation équilibrée et restez hydraté.")
            
        except Exception as e:
            logger.warning(f"Erreur recommandations: {e}")
            recommendations = ["📋 Continuez à suivre vos symptômes quotidiennement."]
        
        return "\n\n".join(recommendations[:5])
    
    def _get_type_recommendation(self, symptom_type: str, avg_level: float) -> str:
        """Obtenir des recommandations spécifiques par type"""
        recommendations = {
            'douleur': "🩹 Douleur: Reposez-vous, appliquez du froid ou de la chaleur selon le cas.",
            'fatigue': "🛌 Fatigue: Dormez 7-8h, limitez la caféine, pratiquez une activité légère.",
            'digestif': "🍲 Problèmes digestifs: Mangez léger, évitez les aliments gras, buvez de l'eau.",
            'respiratoire': "🌬️ Respiration: Reposez-vous, évitez les efforts, consultez si difficulté.",
            'neurologique': "🧠 Migraine/vertiges: Repos dans un endroit calme, évitez la lumière forte.",
            'cardiaque': "❤️ Palpitations: Repos, respiration profonde, consultez si persistant.",
            'musculaire': "💪 Douleurs musculaires: Étirements, repos, application de chaleur.",
            'cutané': "🧴 Problèmes cutanés: Hydratez, évitez les produits agressifs."
        }
        
        base = recommendations.get(symptom_type, "📌 Suivez les recommandations générales.")
        if not math.isnan(avg_level) and avg_level > 6:
            base += " Consultez un médecin si les symptômes persistent."
        
        return base
    
    def _extract_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extraire des insights supplémentaires"""
        insights = {}
        
        if df.empty:
            return insights
        
        try:
            # Période la plus critique
            if 'niveau' in df.columns and not df['niveau'].empty:
                max_idx = df['niveau'].idxmax()
                if max_idx is not None and max_idx < len(df):
                    max_level_row = df.iloc[max_idx]
                    level = int(max_level_row['niveau']) if not math.isnan(max_level_row['niveau']) else 0
                    insights['worst_day'] = {
                        'date': max_level_row['date'].isoformat() if 'date' in max_level_row else datetime.now().isoformat(),
                        'symptom': max_level_row['description'] if 'description' in max_level_row else 'Non spécifié',
                        'level': level
                    }
            
            # Symptôme le plus fréquent
            if 'type' in df.columns and not df['type'].empty:
                most_frequent = df['type'].value_counts().index[0]
                if most_frequent:
                    insights['most_frequent'] = str(most_frequent)
            
            # Évolution globale
            if len(df) > 1 and 'niveau' in df.columns:
                try:
                    values = df['niveau'].values
                    first_third = self._safe_mean(values[:len(values)//3]) if len(values) >= 3 else self._safe_mean(values)
                    last_third = self._safe_mean(values[2*len(values)//3:]) if len(values) >= 3 else self._safe_mean(values)
                    
                    if last_third < first_third * 0.8:
                        insights['overall_trend'] = 'amélioration'
                    elif last_third > first_third * 1.1:
                        insights['overall_trend'] = 'détérioration'
                    else:
                        insights['overall_trend'] = 'stable'
                except:
                    insights['overall_trend'] = 'stable'
            
        except Exception as e:
            logger.warning(f"Erreur insights: {e}")
        
        return insights
    
    def _analyze_severity_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyser la tendance de sévérité"""
        if df.empty or 'niveau' not in df.columns:
            return {}
        
        try:
            levels = df['niveau'].value_counts().sort_index()
            values = df['niveau'].values.tolist()
            
            avg = self._safe_mean(values)
            std = self._safe_std(values)
            max_val = max(values) if values else 0
            min_val = min(values) if values else 0
            
            return {
                'distribution': {str(k): int(v) for k, v in levels.items()},
                'average': float(avg),
                'max': int(max_val),
                'min': int(min_val),
                'std_dev': float(std)
            }
        except Exception as e:
            logger.warning(f"Erreur analyse sévérité: {e}")
            return {}