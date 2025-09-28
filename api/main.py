#!/usr/bin/env python3
"""
CollegeAdvisor API - Main FastAPI application
Consumes RAG service from the data pipeline for college recommendations
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.rag_client import RAGClient
from api.models import (
    RecommendationRequest, 
    RecommendationResponse,
    UserProfile,
    HealthResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CollegeAdvisor API",
    description="API for college recommendations using RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG client
rag_client = RAGClient()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting CollegeAdvisor API...")
    
    # Test RAG service connection
    try:
        health = await rag_client.health_check()
        if health["status"] == "healthy":
            logger.info("✅ RAG service connection established")
        else:
            logger.warning("⚠️ RAG service connection issues detected")
    except Exception as e:
        logger.error(f"❌ Failed to connect to RAG service: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down CollegeAdvisor API...")

# Health and Status Endpoints

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "CollegeAdvisor API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "recommendations": "/api/v1/recommendations",
            "health": "/health",
            "docs": "/docs"
        },
        "rag_service": {
            "status": "connected",
            "collection": "college_advisor@v1.0",
            "model": "llama3:latest"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check RAG service health
        rag_health = await rag_client.health_check()
        
        return HealthResponse(
            status="healthy" if rag_health["status"] == "healthy" else "degraded",
            timestamp=datetime.utcnow(),
            services={
                "api": "healthy",
                "rag_service": rag_health["status"],
                "chromadb": rag_health.get("chromadb", "unknown"),
                "ollama": rag_health.get("ollama", "unknown")
            },
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            services={
                "api": "healthy",
                "rag_service": "unhealthy",
                "chromadb": "unknown",
                "ollama": "unknown"
            },
            version="1.0.0",
            error=str(e)
        )

# Core API Endpoints

@app.post("/api/v1/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get college recommendations based on user query and profile.
    
    This is the main endpoint that consumes the RAG service to provide
    personalized college recommendations.
    """
    try:
        logger.info(f"Recommendation request: {request.query[:50]}...")
        
        # Call RAG service
        rag_result = await rag_client.get_recommendations(
            query=request.query,
            profile=request.profile.model_dump() if request.profile else None,
            n_results=request.max_results,
            filters=request.filters
        )
        
        if "error" in rag_result:
            raise HTTPException(status_code=500, detail=rag_result["error"])
        
        # Format response
        response = RecommendationResponse(
            query=request.query,
            recommendations=rag_result["response"],
            sources=rag_result["sources"],
            metadata={
                "model": rag_result.get("model", "llama3"),
                "retrieval_count": len(rag_result["sources"]),
                "processing_time": rag_result.get("processing_time", 0),
                "timestamp": datetime.utcnow().isoformat()
            },
            profile_used=request.profile.model_dump() if request.profile else None
        )
        
        logger.info(f"Recommendation completed: {len(rag_result['sources'])} sources")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/recommendations/search")
async def search_colleges(
    q: str = Query(..., description="Search query"),
    location: Optional[str] = Query(None, description="Filter by location"),
    gpa_min: Optional[float] = Query(None, description="Minimum GPA requirement"),
    tuition_max: Optional[int] = Query(None, description="Maximum tuition"),
    limit: int = Query(10, description="Maximum number of results")
):
    """
    Search colleges with filters (simplified endpoint).
    """
    try:
        # Build profile from query parameters
        profile = {}
        if gpa_min:
            profile["gpa_range"] = f"{gpa_min}-4.0"
        if location:
            profile["location_preference"] = location
        if tuition_max:
            profile["budget_max"] = tuition_max
        
        # Call RAG service
        rag_result = await rag_client.get_recommendations(
            query=q,
            profile=profile if profile else None,
            n_results=limit
        )
        
        if "error" in rag_result:
            raise HTTPException(status_code=500, detail=rag_result["error"])
        
        return {
            "query": q,
            "results": rag_result["sources"],
            "total": len(rag_result["sources"]),
            "filters_applied": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Development and Testing Endpoints

@app.get("/api/v1/status")
async def get_status():
    """Get detailed system status."""
    try:
        rag_health = await rag_client.health_check()
        
        return {
            "api_status": "operational",
            "rag_service": rag_health,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": {
                "python_version": sys.version,
                "fastapi_version": "0.104.1"  # Update as needed
            }
        }
    except Exception as e:
        return {
            "api_status": "operational",
            "rag_service": {"status": "error", "error": str(e)},
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
