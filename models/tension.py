# meditrack-ai/models/tension.py

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .schemas import Category, SeverityLevel, Stability

class TensionClassifier:
    """Classifieur des valeurs de tension artérielle"""
    
    @staticmethod
    def classify(systolic: int, diastolic: int) -> Category:
        """Classifier la tension en catégories"""
        if systolic < 90 or diastolic < 60:
            return Category.LOW
        elif systolic > 180 or diastolic > 120:
            return Category.CRISIS
        elif systolic > 140 or diastolic > 90:
            return Category.HIGH
        else:
            return Category.NORMAL
    
    @staticmethod
    def get_severity(category: Category) -> SeverityLevel:
        """Obtenir le niveau de sévérité"""
        severity_map = {
            Category.NORMAL: SeverityLevel.NORMAL,
            Category.LOW: SeverityLevel.WARNING,
            Category.HIGH: SeverityLevel.WARNING,
            Category.CRISIS: SeverityLevel.DANGER,
        }
        return severity_map.get(category, SeverityLevel.NORMAL)
    
    @staticmethod
    def get_color(category: Category) -> str:
        """Obtenir la couleur associée"""
        color_map = {
            Category.NORMAL: "#4CAF50",
            Category.LOW: "#2196F3",
            Category.HIGH: "#FF9800",
            Category.CRISIS: "#F44336",
        }
        return color_map.get(category, "#9E9E9E")
    
    @staticmethod
    def get_icon(category: Category) -> str:
        """Obtenir l'icône associée"""
        icon_map = {
            Category.NORMAL: "✅",
            Category.LOW: "⬇️",
            Category.HIGH: "⬆️",
            Category.CRISIS: "🚨",
        }
        return icon_map.get(category, "ℹ️")


class TensionStatistics:
    """Calculateur de statistiques pour les mesures de tension"""
    
    @staticmethod
    def compute_stats(measures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculer les statistiques des mesures"""
        if not measures:
            return {}
        
        df = pd.DataFrame(measures)
        
        # Ajouter la colonne category
        df['category'] = df.apply(
            lambda row: TensionClassifier.classify(
                row['systolic'], 
                row['diastolic']
            ).value if 'systolic' in row and 'diastolic' in row else 'unknown',
            axis=1
        )
        
        stats = {
            "count": len(df),
            "systolic": {
                "mean": df['systolic'].mean(),
                "std": df['systolic'].std(),
                "min": df['systolic'].min(),
                "max": df['systolic'].max(),
                "percentile_25": df['systolic'].quantile(0.25),
                "percentile_75": df['systolic'].quantile(0.75),
            },
            "diastolic": {
                "mean": df['diastolic'].mean(),
                "std": df['diastolic'].std(),
                "min": df['diastolic'].min(),
                "max": df['diastolic'].max(),
                "percentile_25": df['diastolic'].quantile(0.25),
                "percentile_75": df['diastolic'].quantile(0.75),
            },
        }
        
        # Ajouter les statistiques du pouls si disponible
        if 'heart_rate' in df.columns and df['heart_rate'].notna().any():
            stats["heart_rate"] = {
                "mean": df['heart_rate'].mean(),
                "std": df['heart_rate'].std(),
                "min": df['heart_rate'].min(),
                "max": df['heart_rate'].max(),
            }
        
        # Distribution des catégories
        categories = df['category'].value_counts().to_dict()
        stats["categories_distribution"] = categories
        
        return stats
    
    @staticmethod
    def detect_outliers(measures: List[Dict[str, Any]], 
                       z_score_threshold: float = 2.5) -> List[int]:
        """Détecter les outliers dans les mesures"""
        if len(measures) < 3:
            return []
        
        df = pd.DataFrame(measures)
        outliers = set()
        
        for col in ['systolic', 'diastolic']:
            if col in df.columns:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                col_outliers = df[z_scores > z_score_threshold].index.tolist()
                outliers.update(col_outliers)
        
        return list(outliers)


class TensionTrendAnalyzer:
    """Analyseur de tendances des mesures de tension"""
    
    @staticmethod
    def analyze_trend(measures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyser les tendances des mesures"""
        if len(measures) < 3:
            return {
                "available": False,
                "message": "Pas assez de données (minimum 3 mesures)"
            }
        
        df = pd.DataFrame(measures)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Créer un index numérique
        df['day_index'] = (df['date'] - df['date'].min()).dt.days
        
        from sklearn.linear_model import LinearRegression
        
        trends = {}
        strongest_trend = 0
        
        for col in ['systolic', 'diastolic']:
            X = df['day_index'].values.reshape(-1, 1)
            y = df[col].values
            
            model = LinearRegression().fit(X, y)
            trend = float(model.coef_[0])
            r_squared = float(model.score(X, y))
            
            trends[col] = {
                "trend": trend,
                "r_squared": r_squared,
                "intercept": float(model.intercept_),
                "strength": abs(trend) * r_squared
            }
            
            if abs(trend) > abs(strongest_trend):
                strongest_trend = trend
        
        # Déterminer la stabilité
        if abs(strongest_trend) < 0.3:
            stability = Stability.STABLE
        elif strongest_trend > 0:
            stability = Stability.INCREASING
        else:
            stability = Stability.DECREASING
        
        # Volatilité
        volatility = {
            "systolic": df['systolic'].std() / df['systolic'].mean() if df['systolic'].mean() > 0 else 0,
            "diastolic": df['diastolic'].std() / df['diastolic'].mean() if df['diastolic'].mean() > 0 else 0,
        }
        
        return {
            "available": True,
            "stability": stability,
            "trends": trends,
            "volatility": volatility,
            "total_variation": {
                "systolic": float(df['systolic'].max() - df['systolic'].min()),
                "diastolic": float(df['diastolic'].max() - df['diastolic'].min()),
            }
        }


class TensionPredictor:
    """Prédicteur des tendances futures"""
    
    @staticmethod
    def predict_future(measures: List[Dict[str, Any]], 
                      days_ahead: int = 7) -> Dict[str, Any]:
        """Prédire les valeurs futures de tension"""
        if len(measures) < 3:
            return {"available": False}
        
        df = pd.DataFrame(measures)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Créer un index numérique
        df['day_index'] = (df['date'] - df['date'].min()).dt.days
        
        from sklearn.linear_model import LinearRegression
        
        predictions = {}
        
        for col in ['systolic', 'diastolic']:
            X = df['day_index'].values.reshape(-1, 1)
            y = df[col].values
            
            # Régression linéaire
            model = LinearRegression().fit(X, y)
            
            # Prédire les jours futurs
            future_days = np.array([df['day_index'].max() + i + 1 for i in range(days_ahead)])
            future_values = model.predict(future_days.reshape(-1, 1))
            
            predictions[col] = {
                "future_values": future_values.tolist(),
                "trend": float(model.coef_[0]),
                "intercept": float(model.intercept_),
                "r_squared": float(model.score(X, y)),
                "confidence": float(model.score(X, y))
            }
        
        return {
            "available": True,
            "days_ahead": days_ahead,
            "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "predictions": predictions
        }