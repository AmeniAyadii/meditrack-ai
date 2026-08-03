# tests/test_api.py

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Maintenant les imports fonctionnent
from fastapi.testclient import TestClient
from main import app
from config import settings

client = TestClient(app)

class TestAPI:
    
    def test_root_endpoint(self):
        """Tester l'endpoint racine"""
        response = client.get("/")
        assert response.status_code == 200
        assert "MediTrack AI" in response.json()["message"]
    
    def test_health_endpoint(self):
        """Tester l'endpoint de santé"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_analyze_single_measure_unauthorized(self):
        """Tester l'analyse sans clé API"""
        response = client.post(
            "/api/v1/analyze/single",
            json={"systolic": 120, "diastolic": 80}
        )
        assert response.status_code == 401
        assert "Clé API manquante" in response.text
    
    def test_analyze_single_measure(self):
        """Tester l'analyse d'une mesure"""
        response = client.post(
            "/api/v1/analyze/single",
            json={"systolic": 120, "diastolic": 80, "heart_rate": 72},
            headers={"X-API-Key": settings.API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "recommendation" in data
        assert "severity_level" in data
        assert data["severity_level"] == "normal"
    
    def test_analyze_single_measure_high(self):
        """Tester l'analyse d'une mesure élevée"""
        response = client.post(
            "/api/v1/analyze/single",
            json={"systolic": 155, "diastolic": 95},
            headers={"X-API-Key": settings.API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["severity_level"] == "warning"
    
    def test_analyze_trends(self):
        """Tester l'analyse des tendances"""
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
        
        response = client.post(
            "/api/v1/analyze/trends",
            json={"measures": measures},
            headers={"X-API-Key": settings.API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "details" in data
        assert data["details"]["measure_count"] == 10
    
    def test_analyze_trends_insufficient_data(self):
        """Tester l'analyse avec données insuffisantes"""
        measures = [
            {
                'date': datetime.now().isoformat(),
                'systolic': 120,
                'diastolic': 80
            }
        ]
        
        response = client.post(
            "/api/v1/analyze/trends",
            json={"measures": measures},
            headers={"X-API-Key": settings.API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Pas assez de données" in data["summary"]
    
    def test_predict_endpoint(self):
        """Tester l'endpoint de prédiction"""
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
        
        response = client.post(
            "/api/v1/predict",
            json={"measures": measures, "days_ahead": 7},
            headers={"X-API-Key": settings.API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "systolic" in data["predictions"]
    
    def test_risk_assessment_endpoint(self):
        """Tester l'évaluation des risques"""
        measures = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(10):
            measure = {
                'date': (base_date + timedelta(days=i*3)).isoformat(),
                'systolic': 150 + i,
                'diastolic': 90 + i//2,
                'heart_rate': 72
            }
            measures.append(measure)
        
        response = client.post(
            "/api/v1/risk/assess",
            json={"measures": measures},
            headers={"X-API-Key": settings.API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "risk_level" in data
        assert "risk_factors" in data