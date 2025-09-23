"""Data models for the College Advisor pipeline."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Types of documents in the system."""
    UNIVERSITY = "university"
    PROGRAM = "program"
    SUMMER_PROGRAM = "summer_program"
    ADMISSION_REQUIREMENT = "admission_requirement"
    GENERAL_INFO = "general_info"
    # Authentication-related document types
    USER_AUTH_EVENT = "user_auth_event"
    SECURITY_EVENT = "security_event"
    PHONE_VERIFICATION = "phone_verification"
    SOCIAL_AUTH_DATA = "social_auth_data"


class AuthenticationEventType(str, Enum):
    """Types of authentication events."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    SIGNUP = "signup"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    SOCIAL_SIGNIN = "social_signin"
    PHONE_VERIFICATION = "phone_verification"
    EMAIL_VERIFICATION = "email_verification"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class SecurityEventSeverity(str, Enum):
    """Security event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SocialProvider(str, Enum):
    """Social authentication providers."""
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    GITHUB = "github"


class Document(BaseModel):
    """Base document model for all ingested content."""
    
    id: str = Field(..., description="Unique identifier for the document")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Main document content")
    doc_type: DocumentType = Field(..., description="Type of document")
    source_url: Optional[str] = Field(None, description="Original source URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChunkMetadata(BaseModel):
    """Metadata for document chunks."""
    
    document_id: str = Field(..., description="ID of the parent document")
    chunk_index: int = Field(..., description="Index of this chunk within the document")
    chunk_size: int = Field(..., description="Size of the chunk in tokens")
    doc_type: DocumentType = Field(..., description="Type of the parent document")
    
    # University/Program specific metadata
    university_name: Optional[str] = Field(None, description="Name of the university")
    program_name: Optional[str] = Field(None, description="Name of the program")
    program_type: Optional[str] = Field(None, description="Type of program (undergraduate, graduate, etc.)")
    subject_area: Optional[str] = Field(None, description="Subject area or field of study")
    location: Optional[str] = Field(None, description="Geographic location")
    
    # Admission requirements
    gpa_requirement: Optional[float] = Field(None, description="Minimum GPA requirement")
    test_scores: Optional[Dict[str, Any]] = Field(None, description="Required test scores")
    
    # Summer programs
    duration: Optional[str] = Field(None, description="Program duration")
    age_range: Optional[str] = Field(None, description="Target age range")
    cost: Optional[str] = Field(None, description="Program cost information")
    
    # Additional searchable fields
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")


class EmbeddingResult(BaseModel):
    """Result of embedding generation."""
    
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    embedding: List[float] = Field(..., description="Vector embedding")
    model_name: str = Field(..., description="Name of the embedding model used")
    embedding_dim: int = Field(..., description="Dimension of the embedding vector")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessingStats(BaseModel):
    """Statistics from processing operations."""

    total_documents: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    processing_time: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# Authentication-related models

class AuthenticationEvent(BaseModel):
    """Model for authentication events."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: AuthenticationEventType = Field(..., description="Type of authentication event")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    authentication_method: str = Field(..., description="Authentication method used")
    device_type: Optional[str] = Field(None, description="Device type (mobile, desktop, tablet)")
    ip_address: Optional[str] = Field(None, description="IP address of the request")
    location: Optional[str] = Field(None, description="Geographic location")
    session_duration: Optional[int] = Field(None, description="Session duration in seconds")
    success: bool = Field(..., description="Whether the authentication was successful")
    failure_reason: Optional[str] = Field(None, description="Reason for failure if applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SecurityEvent(BaseModel):
    """Model for security events."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of security event")
    severity: SecurityEventSeverity = Field(..., description="Event severity level")
    user_id: Optional[str] = Field(None, description="Associated user ID if applicable")
    timestamp: datetime = Field(..., description="Event timestamp")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    threat_level: str = Field(..., description="Assessed threat level")
    description: str = Field(..., description="Event description")
    action_taken: Optional[str] = Field(None, description="Action taken in response")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    resolved: bool = Field(default=False, description="Whether the event has been resolved")
    resolution_time: Optional[datetime] = Field(None, description="Time when event was resolved")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PhoneVerificationEvent(BaseModel):
    """Model for phone verification events."""

    verification_id: str = Field(..., description="Unique verification identifier")
    user_id: str = Field(..., description="User identifier")
    phone_number: str = Field(..., description="Phone number (hashed/masked)")
    verification_method: str = Field(..., description="Verification method (sms, voice)")
    timestamp: datetime = Field(..., description="Verification timestamp")
    success: bool = Field(..., description="Whether verification was successful")
    attempts: int = Field(default=1, description="Number of verification attempts")
    carrier: Optional[str] = Field(None, description="Phone carrier")
    country_code: Optional[str] = Field(None, description="Country code")
    delivery_time: Optional[float] = Field(None, description="SMS delivery time in seconds")
    failure_reason: Optional[str] = Field(None, description="Reason for failure if applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional verification metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SocialAuthEvent(BaseModel):
    """Model for social authentication events."""

    event_id: str = Field(..., description="Unique event identifier")
    user_id: str = Field(..., description="User identifier")
    provider: SocialProvider = Field(..., description="Social authentication provider")
    timestamp: datetime = Field(..., description="Event timestamp")
    success: bool = Field(..., description="Whether authentication was successful")
    oauth_flow_type: str = Field(..., description="OAuth flow type used")
    permissions_granted: List[str] = Field(default_factory=list, description="Permissions granted by user")
    profile_data_received: Dict[str, Any] = Field(default_factory=dict, description="Profile data received")
    device_type: Optional[str] = Field(None, description="Device type")
    ip_address: Optional[str] = Field(None, description="IP address")
    response_time: Optional[float] = Field(None, description="Provider response time in seconds")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional auth metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    """Enhanced user profile model for personalization."""

    user_id: str = Field(..., description="Unique user identifier")
    email: Optional[str] = Field(None, description="User email (hashed)")
    phone_verified: bool = Field(default=False, description="Whether phone is verified")
    email_verified: bool = Field(default=False, description="Whether email is verified")
    mfa_enabled: bool = Field(default=False, description="Whether MFA is enabled")
    preferred_auth_methods: List[str] = Field(default_factory=list, description="Preferred authentication methods")
    social_providers: List[SocialProvider] = Field(default_factory=list, description="Connected social providers")

    # Personalization data
    education_interests: List[str] = Field(default_factory=list, description="Educational interests")
    preferred_locations: List[str] = Field(default_factory=list, description="Preferred geographic locations")
    academic_level: Optional[str] = Field(None, description="Current academic level")
    target_programs: List[str] = Field(default_factory=list, description="Target program types")

    # Engagement metrics
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_frequency: Optional[str] = Field(None, description="Login frequency pattern")
    session_duration_avg: Optional[float] = Field(None, description="Average session duration")
    platform_preference: Optional[str] = Field(None, description="Preferred platform (iOS, Android, Web)")

    # Privacy settings
    data_sharing_consent: bool = Field(default=False, description="Consent for data sharing")
    analytics_consent: bool = Field(default=False, description="Consent for analytics")
    marketing_consent: bool = Field(default=False, description="Consent for marketing")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
