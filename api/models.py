"""
Pydantic models for the CollegeAdvisor API
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class GPARange(str, Enum):
    """GPA range options."""
    BELOW_2_5 = "below_2.5"
    RANGE_2_5_3_0 = "2.5-3.0"
    RANGE_3_0_3_5 = "3.0-3.5"
    RANGE_3_5_4_0 = "3.5-4.0"
    ABOVE_4_0 = "above_4.0"

class UserProfile(BaseModel):
    """User profile for personalized recommendations."""
    
    # Academic information
    gpa_range: Optional[GPARange] = Field(None, description="GPA range")
    intended_major: Optional[str] = Field(None, description="Intended major or field of study")
    academic_interests: Optional[List[str]] = Field(default_factory=list, description="Academic interests")
    
    # Geographic preferences
    location_preference: Optional[str] = Field(None, description="Preferred location (state, region, etc.)")
    location_flexibility: Optional[bool] = Field(True, description="Willing to consider other locations")
    
    # Financial considerations
    budget_max: Optional[int] = Field(None, description="Maximum budget for tuition")
    financial_aid_needed: Optional[bool] = Field(None, description="Requires financial aid")
    
    # School preferences
    school_size_preference: Optional[str] = Field(None, description="Preferred school size (small, medium, large)")
    school_type_preference: Optional[str] = Field(None, description="Preferred school type (public, private, etc.)")
    
    # Additional preferences
    extracurricular_interests: Optional[List[str]] = Field(
        default_factory=list, description="Extracurricular interests"
    )
    career_goals: Optional[str] = Field(None, description="Career goals or aspirations")

class RecommendationRequest(BaseModel):
    """Request model for college recommendations."""
    
    query: str = Field(..., description="User's question or request", min_length=1, max_length=1000)
    profile: Optional[UserProfile] = Field(None, description="User profile for personalization")
    max_results: int = Field(5, description="Maximum number of results to return", ge=1, le=20)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the best computer science programs for AI research?",
                "profile": {
                    "gpa_range": "3.5-4.0",
                    "intended_major": "Computer Science",
                    "academic_interests": ["Artificial Intelligence", "Machine Learning"],
                    "location_preference": "California",
                    "budget_max": 60000
                },
                "max_results": 5
            }
        }

class DocumentSource(BaseModel):
    """Source document information."""
    
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    document_id: Optional[str] = Field(None, description="Document identifier")

class RecommendationResponse(BaseModel):
    """Response model for college recommendations."""
    
    query: str = Field(..., description="Original user query")
    recommendations: str = Field(..., description="Generated recommendations text")
    sources: List[DocumentSource] = Field(default_factory=list, description="Source documents used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    profile_used: Optional[Dict[str, Any]] = Field(None, description="Profile used for personalization")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the best computer science programs for AI research?",
                "recommendations": "Based on your interest in AI research, I recommend Stanford University and MIT...",
                "sources": [
                    {
                        "content": "Stanford University offers one of the top computer science programs...",
                        "metadata": {
                            "type": "university",
                            "name": "Stanford University",
                            "location": "California, USA"
                        },
                        "relevance_score": 0.95
                    }
                ],
                "metadata": {
                    "model": "llama3",
                    "retrieval_count": 3,
                    "processing_time": 2.5,
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }

class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Individual service statuses")
    version: str = Field(..., description="API version")
    error: Optional[str] = Field(None, description="Error message if unhealthy")

class SearchFilters(BaseModel):
    """Search filters for college search."""
    
    location: Optional[str] = Field(None, description="Location filter")
    gpa_min: Optional[float] = Field(None, description="Minimum GPA requirement", ge=0.0, le=4.0)
    gpa_max: Optional[float] = Field(None, description="Maximum GPA requirement", ge=0.0, le=4.0)
    tuition_min: Optional[int] = Field(None, description="Minimum tuition", ge=0)
    tuition_max: Optional[int] = Field(None, description="Maximum tuition", ge=0)
    acceptance_rate_min: Optional[float] = Field(None, description="Minimum acceptance rate", ge=0.0, le=1.0)
    acceptance_rate_max: Optional[float] = Field(None, description="Maximum acceptance rate", ge=0.0, le=1.0)
    school_type: Optional[str] = Field(None, description="School type (public, private, etc.)")
    majors: Optional[List[str]] = Field(default_factory=list, description="Available majors")

class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")

# Response models for different endpoints
class StatusResponse(BaseModel):
    """System status response."""
    
    api_status: str = Field(..., description="API status")
    rag_service: Dict[str, Any] = Field(default_factory=dict, description="RAG service status")
    timestamp: str = Field(..., description="Status check timestamp")
    environment: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Environment information")

class SearchResponse(BaseModel):
    """Search results response."""
    
    query: str = Field(..., description="Search query")
    results: List[DocumentSource] = Field(default_factory=list, description="Search results")
    total: int = Field(..., description="Total number of results")
    filters_applied: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Filters that were applied")
    pagination: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pagination information")
