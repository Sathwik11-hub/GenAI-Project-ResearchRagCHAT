"""
Data models and schemas for job-related data structures
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class ExperienceLevel(str, Enum):
    """Experience level enumeration"""
    ENTRY = "entry"
    ASSOCIATE = "associate"
    MID = "mid"
    SENIOR = "senior"
    EXECUTIVE = "executive"

class JobType(str, Enum):
    """Job type enumeration"""
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"

class ApplicationStatus(str, Enum):
    """Application status enumeration"""
    PENDING = "pending"
    APPLIED = "applied"
    REVIEWED = "reviewed"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

class JobDetails(BaseModel):
    """Job details data model"""
    
    id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    url: str = Field(..., description="Job posting URL")
    description: str = Field(default="", description="Job description")
    requirements: List[str] = Field(default_factory=list, description="Job requirements")
    salary_range: str = Field(default="", description="Salary range")
    job_type: str = Field(default="", description="Type of job (full-time, part-time, etc.)")
    experience_level: str = Field(default="", description="Required experience level")
    posted_date: str = Field(default="", description="Date when job was posted")
    match_score: Optional[float] = Field(default=None, description="AI matching score (0-1)")
    
    # Additional metadata
    benefits: List[str] = Field(default_factory=list, description="Job benefits")
    skills_required: List[str] = Field(default_factory=list, description="Required skills")
    skills_preferred: List[str] = Field(default_factory=list, description="Preferred skills")
    company_size: str = Field(default="", description="Company size")
    industry: str = Field(default="", description="Company industry")
    remote_friendly: bool = Field(default=False, description="Remote work allowed")
    
    @validator('match_score')
    def validate_match_score(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Match score must be between 0 and 1')
        return v

class JobSearchRequest(BaseModel):
    """Request model for job search"""
    
    keywords: str = Field(..., description="Search keywords")
    location: str = Field(default="", description="Job location")
    experience_level: Optional[ExperienceLevel] = Field(default=None, description="Experience level")
    job_type: Optional[JobType] = Field(default=None, description="Job type")
    company: str = Field(default="", description="Specific company")
    salary_min: Optional[int] = Field(default=None, description="Minimum salary")
    salary_max: Optional[int] = Field(default=None, description="Maximum salary")
    remote_only: bool = Field(default=False, description="Remote jobs only")
    limit: int = Field(default=20, description="Maximum number of results")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v

class JobSearchResponse(BaseModel):
    """Response model for job search"""
    
    success: bool = Field(..., description="Whether the search was successful")
    jobs: List[JobDetails] = Field(default_factory=list, description="List of found jobs")
    total_count: int = Field(default=0, description="Total number of jobs found")
    message: str = Field(default="", description="Response message")
    search_time_ms: Optional[int] = Field(default=None, description="Search time in milliseconds")

class AutoApplyRequest(BaseModel):
    """Request model for auto-apply functionality"""
    
    keywords: str = Field(..., description="Job search keywords")
    location: str = Field(default="", description="Preferred location")
    experience_level: Optional[ExperienceLevel] = Field(default=None, description="Experience level")
    job_type: Optional[JobType] = Field(default=None, description="Job type preference")
    company: str = Field(default="", description="Target companies (optional)")
    
    # Application settings
    max_applications_per_run: int = Field(default=5, description="Max applications per run")
    min_match_score: float = Field(default=0.7, description="Minimum match score to apply")
    generate_cover_letter: bool = Field(default=True, description="Generate custom cover letter")
    custom_message: str = Field(default="", description="Custom application message")
    
    # Scheduling
    schedule_time: Optional[datetime] = Field(default=None, description="When to start auto-apply")
    run_daily: bool = Field(default=False, description="Run daily at scheduled time")
    
    @validator('max_applications_per_run')
    def validate_max_applications(cls, v):
        if v < 1 or v > 20:
            raise ValueError('Max applications per run must be between 1 and 20')
        return v
    
    @validator('min_match_score')
    def validate_min_match_score(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Min match score must be between 0 and 1')
        return v

class AutoApplyResponse(BaseModel):
    """Response model for auto-apply requests"""
    
    success: bool = Field(..., description="Whether auto-apply was started successfully")
    message: str = Field(..., description="Response message")
    process_id: str = Field(default="", description="Process identifier")
    estimated_duration: Optional[int] = Field(default=None, description="Estimated duration in minutes")

class ApplicationRecord(BaseModel):
    """Model for tracking job applications"""
    
    id: str = Field(..., description="Application record ID")
    job_id: str = Field(..., description="Job ID")
    job_title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    applied_at: datetime = Field(..., description="Application timestamp")
    status: ApplicationStatus = Field(default=ApplicationStatus.APPLIED, description="Application status")
    match_score: Optional[float] = Field(default=None, description="Job match score")
    cover_letter_generated: bool = Field(default=False, description="Whether cover letter was generated")
    success: bool = Field(default=True, description="Whether application was successful")
    error_message: str = Field(default="", description="Error message if failed")
    
    # Follow-up tracking
    follow_up_date: Optional[datetime] = Field(default=None, description="When to follow up")
    response_received: bool = Field(default=False, description="Response received from company")
    interview_scheduled: bool = Field(default=False, description="Interview scheduled")

class UserProfile(BaseModel):
    """User profile model"""
    
    # Personal information
    name: str = Field(default="", description="Full name")
    email: str = Field(default="", description="Email address")
    phone: str = Field(default="", description="Phone number")
    location: str = Field(default="", description="Current location")
    
    # Professional information
    title: str = Field(default="", description="Current job title")
    summary: str = Field(default="", description="Professional summary")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    years_experience: int = Field(default=0, description="Years of experience")
    
    # Preferences
    preferred_locations: List[str] = Field(default_factory=list, description="Preferred job locations")
    preferred_job_types: List[JobType] = Field(default_factory=list, description="Preferred job types")
    target_salary_min: Optional[int] = Field(default=None, description="Target minimum salary")
    target_salary_max: Optional[int] = Field(default=None, description="Target maximum salary")
    remote_preference: bool = Field(default=False, description="Prefers remote work")
    
    # Experience and education
    experience: List[Dict[str, Any]] = Field(default_factory=list, description="Work experience")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Education history")
    certifications: List[Dict[str, Any]] = Field(default_factory=list, description="Certifications")
    projects: List[Dict[str, Any]] = Field(default_factory=list, description="Notable projects")

class JobMatchExplanation(BaseModel):
    """Model for explaining job match scores"""
    
    job_id: str = Field(..., description="Job ID")
    overall_score: float = Field(..., description="Overall match score")
    
    breakdown: Dict[str, float] = Field(
        default_factory=dict, 
        description="Score breakdown by category"
    )
    
    matching_skills: List[str] = Field(
        default_factory=list, 
        description="Skills that match"
    )
    
    missing_skills: List[str] = Field(
        default_factory=list, 
        description="Skills mentioned in job but not in profile"
    )
    
    recommendation: str = Field(
        default="", 
        description="Recommendation based on match"
    )
    
    confidence: float = Field(
        default=0.0, 
        description="Confidence in the match score"
    )

class CoverLetterRequest(BaseModel):
    """Request model for cover letter generation"""
    
    job_id: str = Field(..., description="Job ID")
    tone: str = Field(default="professional", description="Tone of the cover letter")
    template: Optional[str] = Field(default=None, description="Custom template")
    custom_points: List[str] = Field(
        default_factory=list, 
        description="Custom points to include"
    )
    
    @validator('tone')
    def validate_tone(cls, v):
        allowed_tones = ['professional', 'casual', 'enthusiastic', 'formal']
        if v not in allowed_tones:
            raise ValueError(f'Tone must be one of: {", ".join(allowed_tones)}')
        return v

class CoverLetterResponse(BaseModel):
    """Response model for cover letter generation"""
    
    success: bool = Field(..., description="Whether generation was successful")
    cover_letter: str = Field(default="", description="Generated cover letter")
    word_count: int = Field(default=0, description="Word count of the letter")
    message: str = Field(default="", description="Response message")
    validation: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Validation results"
    )

class SystemStats(BaseModel):
    """System statistics model"""
    
    total_jobs_scraped: int = Field(default=0, description="Total jobs scraped")
    total_applications: int = Field(default=0, description="Total applications sent")
    applications_today: int = Field(default=0, description="Applications sent today")
    success_rate: float = Field(default=0.0, description="Application success rate")
    average_match_score: float = Field(default=0.0, description="Average match score")
    
    # System health
    is_scraper_running: bool = Field(default=False, description="Scraper status")
    is_auto_apply_running: bool = Field(default=False, description="Auto-apply status")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")
    
    # Vector store stats
    documents_indexed: int = Field(default=0, description="Documents in vector store")
    embeddings_cached: int = Field(default=0, description="Cached embeddings")

# Export all models for easy importing
__all__ = [
    'JobDetails',
    'JobSearchRequest', 
    'JobSearchResponse',
    'AutoApplyRequest',
    'AutoApplyResponse', 
    'ApplicationRecord',
    'UserProfile',
    'JobMatchExplanation',
    'CoverLetterRequest',
    'CoverLetterResponse',
    'SystemStats',
    'ExperienceLevel',
    'JobType',
    'ApplicationStatus'
]