"""
FastAPI main application entry point for CampusBot Query Service.
This microservice handles AI-powered question answering using RAG (Retrieval Augmented Generation).

ARCHITECTURE ROLE:
- Receives questions from Spring Boot backend
- Searches ChromaDB for relevant document chunks
- Generates AI responses using Gemini API
- Returns answers back to Spring Boot

SERVICE ENDPOINTS:
- GET /health: Health check for monitoring
- POST /query: Main question answering endpoint

DEPLOYMENT:
- Runs as Docker container "query-service"
- Exposed on port 8000
- Called by Spring Boot QueryService.java
"""

from fastapi import FastAPI
from .chat_router import router  # Import query endpoint router
from ..models.HealthyResponse import HealthyResponse

try:
    # Initialize FastAPI application
    app = FastAPI()
    
    # Register chat router (adds /query endpoint)
    app.include_router(router)
    
except Exception as e:
    # Fatal error during initialization
    print(e)


@app.get("/health")
def healthChecker():
    """
    Health check endpoint for monitoring service availability.
    
    PURPOSE:
    - Docker health checks
    - Load balancer health checks
    - Kubernetes readiness/liveness probes
    - Monitoring systems (Prometheus, etc.)
    
    Returns:
        HealthyResponse: {"status": "Healthy"}
    """
    healthyResponse = HealthyResponse(status="Healthy")
    return healthyResponse