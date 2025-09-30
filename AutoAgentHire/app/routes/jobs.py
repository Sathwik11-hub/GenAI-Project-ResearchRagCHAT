"""
Job search and application API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
import asyncio

from app.services.job_scraper import JobScraperService
from app.services.matcher import JobMatcherService
from app.services.auto_apply import AutoApplyService
from app.models.job_schema import (
    JobSearchRequest, 
    JobSearchResponse, 
    JobDetails, 
    AutoApplyRequest,
    AutoApplyResponse
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# Dependency injection
def get_job_scraper():
    return JobScraperService()

def get_job_matcher():
    return JobMatcherService()

def get_auto_apply():
    return AutoApplyService()

@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    request: JobSearchRequest,
    job_scraper: JobScraperService = Depends(get_job_scraper)
):
    """
    Search for jobs based on criteria
    """
    try:
        logger.info(f"Searching jobs with criteria: {request.dict()}")
        
        jobs = await job_scraper.search_jobs(
            keywords=request.keywords,
            location=request.location,
            experience_level=request.experience_level,
            job_type=request.job_type,
            company=request.company,
            limit=request.limit
        )
        
        return JobSearchResponse(
            success=True,
            jobs=jobs,
            total_count=len(jobs),
            message=f"Found {len(jobs)} jobs"
        )
        
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

@router.get("/{job_id}", response_model=JobDetails)
async def get_job_details(
    job_id: str,
    job_scraper: JobScraperService = Depends(get_job_scraper)
):
    """
    Get detailed information about a specific job
    """
    try:
        job_details = await job_scraper.get_job_details(job_id)
        
        if not job_details:
            raise HTTPException(status_code=404, detail="Job not found")
            
        return job_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting job details: {str(e)}")

@router.post("/match", response_model=List[JobDetails])
async def match_jobs_to_profile(
    request: JobSearchRequest,
    job_scraper: JobScraperService = Depends(get_job_scraper),
    job_matcher: JobMatcherService = Depends(get_job_matcher)
):
    """
    Find jobs that match the user's profile and preferences
    """
    try:
        # First search for jobs
        jobs = await job_scraper.search_jobs(
            keywords=request.keywords,
            location=request.location,
            experience_level=request.experience_level,
            job_type=request.job_type,
            company=request.company,
            limit=request.limit or 100
        )
        
        # Then match against user profile
        matched_jobs = await job_matcher.match_jobs(jobs)
        
        # Sort by match score
        matched_jobs.sort(key=lambda x: x.match_score or 0, reverse=True)
        
        return matched_jobs[:request.limit or 20]
        
    except Exception as e:
        logger.error(f"Error matching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error matching jobs: {str(e)}")

@router.post("/auto-apply", response_model=AutoApplyResponse)
async def auto_apply_to_jobs(
    request: AutoApplyRequest,
    background_tasks: BackgroundTasks,
    auto_apply: AutoApplyService = Depends(get_auto_apply)
):
    """
    Automatically apply to jobs based on criteria
    """
    try:
        logger.info(f"Starting auto-apply process with criteria: {request.dict()}")
        
        # Add the auto-apply task to background tasks
        background_tasks.add_task(
            auto_apply.start_auto_apply_process,
            request
        )
        
        return AutoApplyResponse(
            success=True,
            message="Auto-apply process started successfully",
            process_id=f"auto_apply_{request.keywords.replace(' ', '_')}"
        )
        
    except Exception as e:
        logger.error(f"Error starting auto-apply: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting auto-apply: {str(e)}")

@router.get("/applications/status")
async def get_application_status():
    """
    Get status of current and past job applications
    """
    try:
        # This would typically query a database for application history
        return {
            "success": True,
            "applications_today": 0,
            "total_applications": 0,
            "success_rate": 0.0,
            "recent_applications": []
        }
        
    except Exception as e:
        logger.error(f"Error getting application status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting application status: {str(e)}")

@router.post("/pause-auto-apply")
async def pause_auto_apply():
    """
    Pause the current auto-apply process
    """
    try:
        # Implementation would depend on how the background process is managed
        return {"success": True, "message": "Auto-apply process paused"}
        
    except Exception as e:
        logger.error(f"Error pausing auto-apply: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error pausing auto-apply: {str(e)}")