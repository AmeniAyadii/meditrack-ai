# tests/test_analyzer.py

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Maintenant les imports fonctionnent
from models.schemas import SingleMeasure, SeverityLevel
from services.analyzer import TensionAnalyzer

class TestTensionAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        return TensionAnalyzer()
    
    @pytest.fixture
    def normal_measure(self):
        return SingleMeasure(
            systolic=120,
            diastolic=80,
            heart_rate=72,
            measure_date=datetime.now().isoformat()
        )
    
    @pytest.fixture
    def high_measure(self):
        return SingleMeasure(
            systolic=155,
            diastolic=95,
            heart_rate=85,
            measure_date=datetime.now().isoformat()
        )
    
    @pytest.fixture
    def crisis_measure(self):
        return SingleMeasure(
            systolic=185,
            diastolic=115,
            heart_rate=95,
            measure_date=datetime.now().isoformat()
        )
    
    def test_analyze_normal_measure(self, analyzer, normal_measure):
        """Tester l'analyse d'une mesure normale"""
        result = analyzer.analyze_single_measure(normal_measure)
        
        assert result.severity_level == SeverityLevel.NORMAL
        assert "normale" in result.summary.lower()
        assert result.details['category'] == 'normal'
    
    def test_analyze_high_measure(self, analyzer, high_measure):
        """Tester l'analyse d'une mesure élevée"""
        result = analyzer.analyze_single_measure(high_measure)
        
        assert result.severity_level == SeverityLevel.WARNING
        assert "hypertension" in result.summary.lower() or "élevée" in result.summary.lower()
        assert result.details['category'] == 'high'
    
    def test_analyze_crisis_measure(self, analyzer, crisis_measure):
        """Tester l'analyse d'une mesure en crise"""
        result = analyzer.analyze_single_measure(crisis_measure)
        
        assert result.severity_level == SeverityLevel.DANGER
        assert "crise" in result.summary.lower() or "urgent" in result.summary.lower()
        assert result.details['category'] == 'crisis'
    
    def test_analyze_trends(self, analyzer):
        """Tester l'analyse des tendances"""
        # Créer des mesures fictives
        measures = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(10):
            measure = {
                'date': (base_date + timedelta(days=i*3)).isoformat(),
                'systolic': 120 + i * 2,
                'diastolic': 80 + i,
                'heart_rate': 72
            }
            measures.append(measure)
        
        result = analyzer.analyze_trends(measures)
        
        assert result.details['measure_count'] == 10
        assert result.severity_level in [SeverityLevel.NORMAL, SeverityLevel.WARNING]
        assert 'trend_systolic' in result.details
    
    def test_analyze_trends_insufficient_data(self, analyzer):
        """Tester l'analyse avec des données insuffisantes"""
        measures = [
            {
                'date': datetime.now().isoformat(),
                'systolic': 120,
                'diastolic': 80
            }
        ]
        
        result = analyzer.analyze_trends(measures)
        
        assert "pas assez de données" in result.summary.lower()