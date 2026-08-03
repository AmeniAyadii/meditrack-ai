
### 6.1 Middleware de logging


# meditrack-ai/utils/middleware.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from utils.logger import logger
import json

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger les requêtes HTTP"""
    
    async def dispatch(self, request: Request, call_next):
        # Démarrer le timer
        start_time = time.time()
        
        # Logger la requête
        logger.info(
            f"Requête: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        try:
            # Exécuter la requête
            response = await call_next(request)
            
            # Calculer le temps
            process_time = time.time() - start_time
            
            # Logger la réponse
            logger.info(
                f"Réponse: {response.status_code} ({process_time:.3f}s)",
                extra={
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "path": request.url.path
                }
            )
            
            # Ajouter l'en-tête de temps
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Logger l'erreur
            logger.error(
                f"Erreur lors du traitement: {str(e)}",
                extra={
                    "path": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise