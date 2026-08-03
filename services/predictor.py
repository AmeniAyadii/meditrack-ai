# meditrack-ai/services/predictor.py

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
from models.schemas import Stability
from utils.logger import logger

class AdvancedPredictor:
    """Prédicteur avancé avec différents modèles"""
    
    def __init__(self):
        self.models = {}
        logger.info("Prédicteur avancé initialisé")
    
    def predict_with_linear_regression(self, 
                                       df: pd.DataFrame, 
                                       column: str,
                                       days_ahead: int = 7) -> Dict[str, Any]:
        """
        Prédire avec régression linéaire
        
        Args:
            df: DataFrame avec les mesures
            column: Colonne à prédire
            days_ahead: Nombre de jours à prédire
        
        Returns:
            Dict contenant les prédictions
        """
        # Préparer les données
        X = df['day_index'].values.reshape(-1, 1)
        y = df[column].values
        
        # Entraîner le modèle
        model = LinearRegression()
        model.fit(X, y)
        
        # Prédire les jours futurs
        future_days = np.array([df['day_index'].max() + i + 1 for i in range(days_ahead)])
        future_values = model.predict(future_days.reshape(-1, 1))
        
        return {
            "model": "linear_regression",
            "future_values": future_values.tolist(),
            "trend": float(model.coef_[0]),
            "intercept": float(model.intercept_),
            "r2_score": float(model.score(X, y)),
            "confidence": float(model.score(X, y))
        }
    
    def predict_with_polynomial(self, 
                                df: pd.DataFrame, 
                                column: str,
                                degree: int = 2,
                                days_ahead: int = 7) -> Dict[str, Any]:
        """
        Prédire avec régression polynomiale
        
        Args:
            df: DataFrame avec les mesures
            column: Colonne à prédire
            degree: Degré du polynôme
            days_ahead: Nombre de jours à prédire
        
        Returns:
            Dict contenant les prédictions
        """
        # Préparer les données
        X = df['day_index'].values.reshape(-1, 1)
        y = df[column].values
        
        # Créer le pipeline polynomial
        pipeline = Pipeline([
            ('poly', PolynomialFeatures(degree=degree, include_bias=False)),
            ('linear', LinearRegression())
        ])
        
        pipeline.fit(X, y)
        
        # Prédire les jours futurs
        future_days = np.array([df['day_index'].max() + i + 1 for i in range(days_ahead)])
        future_values = pipeline.predict(future_days.reshape(-1, 1))
        
        # Calculer le score
        y_pred = pipeline.predict(X)
        r2 = r2_score(y, y_pred)
        
        return {
            "model": f"polynomial_{degree}",
            "future_values": future_values.tolist(),
            "r2_score": float(r2),
            "confidence": float(r2)
        }
    
    def predict_ensemble(self, 
                         df: pd.DataFrame, 
                         days_ahead: int = 7) -> Dict[str, Any]:
        """
        Prédire en utilisant un ensemble de modèles
        
        Args:
            df: DataFrame avec les mesures
            days_ahead: Nombre de jours à prédire
        
        Returns:
            Dict contenant les prédictions
        """
        predictions = {}
        
        for col in ['systolic', 'diastolic']:
            # Régression linéaire
            linear = self.predict_with_linear_regression(df, col, days_ahead)
            
            # Régression polynomiale (degré 2)
            poly = self.predict_with_polynomial(df, col, 2, days_ahead)
            
            # Ensemble: moyenne pondérée
            weight_linear = linear['r2_score']
            weight_poly = poly['r2_score']
            total_weight = weight_linear + weight_poly
            
            if total_weight > 0:
                combined_values = [
                    (l * weight_linear + p * weight_poly) / total_weight
                    for l, p in zip(linear['future_values'], poly['future_values'])
                ]
                confidence = max(weight_linear, weight_poly)
            else:
                combined_values = linear['future_values']
                confidence = 0.5
            
            predictions[col] = {
                "future_values": combined_values,
                "linear_prediction": linear,
                "polynomial_prediction": poly,
                "confidence": float(confidence),
                "r2_score": float(confidence)
            }
        
        return {
            "available": True,
            "days_ahead": days_ahead,
            "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "predictions": predictions,
            "ensemble_confidence": float(np.mean([p['confidence'] for p in predictions.values()]))
        }

class RiskPredictor:
    """Prédicteur des risques pour la santé"""
    
    @staticmethod
    def assess_risk(measures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Évaluer les risques pour la santé à partir des mesures
        
        Args:
            measures: Liste des mesures
        
        Returns:
            Dict contenant l'évaluation des risques
        """
        if len(measures) < 3:
            return {
                "available": False,
                "message": "Pas assez de données (minimum 3 mesures)"
            }
        
        df = pd.DataFrame(measures)
        
        # Risque cardiovasculaire basé sur la tension
        risk_factors = []
        score = 0
        
        # 1. Tension moyenne
        avg_systolic = df['systolic'].mean()
        avg_diastolic = df['diastolic'].mean()
        
        if avg_systolic > 140 or avg_diastolic > 90:
            risk_factors.append("Tension élevée persistante")
            score += 2
        
        # 2. Variabilité
        std_systolic = df['systolic'].std()
        if std_systolic > 15:
            risk_factors.append("Variabilité importante de la tension")
            score += 1
        
        # 3. Tendance
        if len(df) > 5:
            from sklearn.linear_model import LinearRegression
            X = np.arange(len(df)).reshape(-1, 1)
            y = df['systolic'].values
            
            model = LinearRegression().fit(X, y)
            trend = model.coef_[0]
            
            if trend > 0.5:
                risk_factors.append("Tendance à la hausse significative")
                score += 2
            elif trend > 0.2:
                risk_factors.append("Légère tendance à la hausse")
                score += 1
        
        # 4. Pics de tension
        max_systolic = df['systolic'].max()
        if max_systolic > 160:
            risk_factors.append("Pics de tension élevée")
            score += 1
        
        # Déterminer le niveau de risque
        if score >= 4:
            risk_level = "Élevé"
            recommendation = "🚨 Risque cardiovasculaire élevé. Consultez un médecin rapidement."
        elif score >= 2:
            risk_level = "Modéré"
            recommendation = "⚠️ Risque modéré. Surveillez régulièrement votre tension et consultez si nécessaire."
        else:
            risk_level = "Faible"
            recommendation = "✅ Risque faible. Continuez à surveiller votre tension régulièrement."
        
        return {
            "available": True,
            "risk_level": risk_level,
            "risk_score": score,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "details": {
                "avg_systolic": float(avg_systolic),
                "avg_diastolic": float(avg_diastolic),
                "std_systolic": float(std_systolic),
                "max_systolic": float(max_systolic),
                "measure_count": len(df)
            }
        }