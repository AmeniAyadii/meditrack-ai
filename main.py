# meditrack-ai/main.py

from fastapi import FastAPI, HTTPException, Depends, Security, status, Request  # 🔥 AJOUTER Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from datetime import datetime
import time

from config import settings
from models.schemas import (
    SingleMeasure, SingleAnalysisResponse, TrendAnalysisResponse,
    ErrorResponse, HealthResponse, SeverityLevel
)
from services.analyzer import TensionAnalyzer
from services.predictor import AdvancedPredictor, RiskPredictor
from utils.logger import logger, get_logger
from utils.validators import validate_measures, sanitize_input
from utils.middleware import RequestLoggingMiddleware
from services.symptom_analyzer import SymptomAnalyzer

# ============================================
# INITIALISATION DE L'APPLICATION
# ============================================

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Sécurité
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ============================================
# MIDDLEWARES
# ============================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging des requêtes
app.add_middleware(RequestLoggingMiddleware)

# ============================================
# DEPENDANCES
# ============================================

def get_analyzer() -> TensionAnalyzer:
    """Obtenir l'analyseur de tension"""
    return TensionAnalyzer()

def get_predictor() -> AdvancedPredictor:
    """Obtenir le prédicteur avancé"""
    return AdvancedPredictor()

def get_risk_predictor() -> RiskPredictor:
    """Obtenir le prédicteur de risques"""
    return RiskPredictor()

# 🔥 FONCTION DE VÉRIFICATION DÉSACTIVÉE POUR LES TESTS
async def verify_api_key(api_key: str = Security(api_key_header)):
    """Vérifier la clé API - DÉSACTIVÉ POUR LES TESTS"""
    # 🔥 Retourne toujours True pour les tests
    return "dev-api-key"
    
    # Code original commenté
    # if api_key is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Clé API manquante"
    #     )
    # 
    # if api_key != settings.API_KEY:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Clé API invalide"
    #     )
    # 
    # return api_key

# ============================================
# VARIABLES GLOBALES
# ============================================

start_time = time.time()

# ============================================
# INITIALISATION DES SERVICES
# ============================================

# 🔥 Initialiser l'analyseur de symptômes
symptom_analyzer = SymptomAnalyzer()

# ============================================
# ENDPOINTS
# ============================================

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Endpoint racine"""
    return {
        "message": f"🤖 {settings.API_TITLE}",
        "version": settings.API_VERSION,
        "status": "Operational",
        "endpoints": {
            "docs": "/api/docs",
            "health": "/api/health",
            "analyze_single": "/api/v1/analyze/single",
            "analyze_trends": "/api/v1/analyze/trends",
            "predict": "/api/v1/predict",
            "risk_assessment": "/api/v1/risk/assess",
            "analyze_symptoms": "/api/v1/symptoms/analyze"
        }
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Vérifier l'état du service"""
    uptime = time.time() - start_time
    
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        uptime=uptime,
        timestamp=datetime.now().isoformat()
    )

@app.post(
    "/api/v1/analyze/single",
    response_model=SingleAnalysisResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}}
)
async def analyze_single_measure(
    measure: SingleMeasure,
    analyzer: TensionAnalyzer = Depends(get_analyzer),
    # 🔥 COMMENTÉ POUR LES TESTS
    # api_key: str = Depends(verify_api_key)
):
    """
    Analyser une mesure individuelle de tension
    
    - **systolic**: Pression systolique (50-250 mmHg)
    - **diastolic**: Pression diastolique (30-160 mmHg)
    - **heart_rate**: Fréquence cardiaque (optionnel, 20-220 bpm)
    - **measure_date**: Date de la mesure (optionnel, format ISO)
    - **notes**: Notes supplémentaires (optionnel)
    """
    try:
        logger.info(f"Analyse d'une mesure reçue: {measure.systolic}/{measure.diastolic}")
        result = analyzer.analyze_single_measure(measure)
        return result
    
    except ValueError as e:
        logger.error(f"Erreur de validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="VALIDATION_ERROR",
                message=str(e),
                timestamp=datetime.now().isoformat()
            ).dict()
        )
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message="Une erreur est survenue lors de l'analyse",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            ).dict()
        )

@app.post(
    "/api/v1/analyze/trends",
    response_model=TrendAnalysisResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def analyze_trends(
    analysis_data: Dict[str, Any],
    analyzer: TensionAnalyzer = Depends(get_analyzer)
    # 🔥 LIGNE SUPPRIMÉE - PLUS DE VÉRIFICATION
    # api_key: str = Depends(verify_api_key)
):
    """
    Analyser les tendances à partir d'un historique de mesures
    
    Requiert au moins 3 mesures
    """
    try:
        logger.info(f"Analyse des tendances reçue: {len(analysis_data.get('measures', []))} mesures")
        
        # Valider les données
        measures = analysis_data.get('measures', [])
        if not measures:
            raise ValueError("Liste de mesures vide")
        
        if len(measures) < 3:
            # Retourner une réponse directe sans utiliser le modèle
            return TrendAnalysisResponse(
                summary="📊 Pas assez de données pour une analyse de tendance",
                recommendation="Continuez à enregistrer vos mesures régulièrement. L'analyse nécessite au moins 3 mesures.",
                severity_level=SeverityLevel.NORMAL,
                details={"message": "Insufficient data", "minimum_required": 3}
            )
        
        # Analyser
        result = analyzer.analyze_trends(measures)
        
        # Vérifier que le résultat n'est pas None
        if result is None:
            raise ValueError("L'analyse a retourné un résultat vide")
        
        return result
    
    except ValueError as e:
        logger.error(f"Erreur de validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="VALIDATION_ERROR",
                message=str(e),
                timestamp=datetime.now().isoformat()
            ).dict()
        )
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message="Une erreur est survenue lors de l'analyse",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            ).dict()
        )

@app.post("/api/v1/predict")
async def predict_future(
    data: Dict[str, Any],
    predictor: AdvancedPredictor = Depends(get_predictor)
    # 🔥 COMMENTÉ POUR LES TESTS
    # api_key: str = Depends(verify_api_key)
):
    """Prédire les futures valeurs de tension"""
    try:
        measures = data.get('measures', [])
        days_ahead = data.get('days_ahead', 7)
        
        if not measures:
            raise ValueError("Liste de mesures vide")
        
        if len(measures) < 3:
            return {
                "available": False,
                "message": "Pas assez de données (minimum 3 mesures)"
            }
        
        import pandas as pd
        df = pd.DataFrame(measures)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df['day_index'] = (df['date'] - df['date'].min()).dt.days
        
        predictions = predictor.predict_ensemble(df, days_ahead)
        return predictions
    
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="PREDICTION_ERROR",
                message="Erreur lors de la prédiction",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            ).dict()
        )

@app.post("/api/v1/risk/assess")
async def assess_risk(
    data: Dict[str, Any],
    risk_predictor: RiskPredictor = Depends(get_risk_predictor)
    # 🔥 COMMENTÉ POUR LES TESTS
    # api_key: str = Depends(verify_api_key)
):
    """Évaluer les risques pour la santé"""
    try:
        measures = data.get('measures', [])
        
        if not measures:
            raise ValueError("Liste de mesures vide")
        
        if len(measures) < 3:
            return {
                "available": False,
                "message": "Pas assez de données (minimum 3 mesures)"
            }
        
        result = risk_predictor.assess_risk(measures)
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation des risques: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="RISK_ASSESSMENT_ERROR",
                message="Erreur lors de l'évaluation des risques",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            ).dict()
        )

# ============================================
# 🔥 ENDPOINT D'ANALYSE DES SYMPTÔMES
# ============================================

@app.post("/api/v1/symptoms/analyze")
async def analyze_symptoms(
    request: Request,  # 🔥 Request est maintenant importé
    # api_key: str = Depends(verify_api_key)  # Optionnel
):
    """
    Analyser les symptômes avec IA
    
    Requête:
    {
        "symptoms": [
            {
                "id": 1,
                "description": "Mal de tête",
                "type": "neurologique",
                "niveau": 7,
                "status": "actif",
                "date_enregistrement": "2024-01-01T10:00:00"
            }
        ]
    }
    """
    try:
        data = await request.json()
        symptoms = data.get('symptoms', [])
        
        if not symptoms:
            raise HTTPException(status_code=400, detail="Aucun symptôme fourni")
        
        logger.info(f"Analyse IA demandée pour {len(symptoms)} symptômes")
        
        result = symptom_analyzer.analyze_symptoms(symptoms)
        
        return {
            "success": True,
            "data": result,
            "message": "Analyse terminée avec succès"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# GESTIONNAIRES D'EXCEPTIONS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Gestionnaire des exceptions HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=str(exc.detail) if isinstance(exc.detail, str) else str(exc.detail),
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Gestionnaire des exceptions générales"""
    logger.error(f"Exception non gérée: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="Une erreur interne est survenue",
            details={"error": str(exc)} if settings.API_DEBUG else None,
            timestamp=datetime.now().isoformat()
        ).dict()
    )

# ============================================
# DÉMARRAGE
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Démarrage de {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"📍 Host: {settings.API_HOST}, Port: {settings.API_PORT}")
    logger.info(f"📚 Documentation: http://{settings.API_HOST}:{settings.API_PORT}/api/docs")
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )