"""
Automated job application flow service
"""

import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

from app.config import settings
from app.models.job_schema import JobDetails, AutoApplyRequest
from app.services.job_scraper import JobScraperService
from app.services.matcher import JobMatcherService
from app.services.cover_letter_generator import CoverLetterGeneratorService
from automation.linkedin_bot import LinkedInBot
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class AutoApplyService:
    """Service for automating the job application process"""
    
    def __init__(self):
        self.job_scraper = JobScraperService()
        self.job_matcher = JobMatcherService()
        self.cover_letter_generator = CoverLetterGeneratorService()
        self.linkedin_bot = LinkedInBot()
        
        self.is_running = False
        self.applications_today = 0
        self.application_history = []
        self.last_application_time = None
    
    async def start_auto_apply_process(self, request: AutoApplyRequest):
        """Start the automated job application process"""
        
        try:
            logger.info("Starting auto-apply process")
            self.is_running = True
            
            # Load user profile for matching
            await self.job_matcher.load_user_profile()
            
            while self.is_running and self.applications_today < settings.MAX_APPLICATIONS_PER_DAY:
                try:
                    # Search for jobs
                    jobs = await self._search_suitable_jobs(request)
                    
                    if not jobs:
                        logger.info("No suitable jobs found, waiting before next search")
                        await asyncio.sleep(300)  # Wait 5 minutes
                        continue
                    
                    # Apply to jobs
                    for job in jobs:
                        if not self.is_running or self.applications_today >= settings.MAX_APPLICATIONS_PER_DAY:
                            break
                        
                        success = await self._apply_to_job(job, request)
                        
                        if success:
                            self.applications_today += 1
                            logger.info(f"Applied to {job.title} at {job.company} ({self.applications_today}/{settings.MAX_APPLICATIONS_PER_DAY})")
                        
                        # Wait between applications
                        await self._wait_between_applications()
                    
                    # Wait before searching for more jobs
                    await asyncio.sleep(1800)  # Wait 30 minutes
                    
                except Exception as e:
                    logger.error(f"Error in auto-apply loop: {str(e)}")
                    await asyncio.sleep(300)  # Wait 5 minutes before retrying
            
            logger.info("Auto-apply process completed")
            self.is_running = False
            
        except Exception as e:
            logger.error(f"Error in auto-apply process: {str(e)}")
            self.is_running = False
    
    async def _search_suitable_jobs(self, request: AutoApplyRequest) -> List[JobDetails]:
        """Search for jobs that match the criteria and user profile"""
        
        try:
            # Search for jobs
            all_jobs = await self.job_scraper.search_jobs(
                keywords=request.keywords,
                location=request.location,
                experience_level=request.experience_level,
                job_type=request.job_type,
                company=request.company,
                limit=50  # Get more jobs for filtering
            )
            
            if not all_jobs:
                return []
            
            # Filter out already applied jobs
            new_jobs = await self._filter_applied_jobs(all_jobs)
            
            # Match jobs to user profile
            matched_jobs = await self.job_matcher.match_jobs(new_jobs)
            
            # Filter by minimum match score
            min_score = request.min_match_score or 0.7
            suitable_jobs = [job for job in matched_jobs if (job.match_score or 0) >= min_score]
            
            # Sort by match score and limit
            suitable_jobs.sort(key=lambda x: x.match_score or 0, reverse=True)
            
            return suitable_jobs[:request.max_applications_per_run or 5]
            
        except Exception as e:
            logger.error(f"Error searching suitable jobs: {str(e)}")
            return []
    
    async def _filter_applied_jobs(self, jobs: List[JobDetails]) -> List[JobDetails]:
        """Filter out jobs that have already been applied to"""
        
        try:
            applied_job_ids = {app["job_id"] for app in self.application_history}
            new_jobs = [job for job in jobs if job.id not in applied_job_ids]
            
            logger.info(f"Filtered {len(jobs) - len(new_jobs)} already applied jobs")
            return new_jobs
            
        except Exception as e:
            logger.warning(f"Error filtering applied jobs: {str(e)}")
            return jobs
    
    async def _apply_to_job(self, job: JobDetails, request: AutoApplyRequest) -> bool:
        """Apply to a specific job"""
        
        try:
            logger.info(f"Applying to {job.title} at {job.company}")
            
            # Generate cover letter if needed
            cover_letter = None
            if request.generate_cover_letter:
                cover_letter = await self.cover_letter_generator.generate_cover_letter(job)
            
            # Use LinkedIn bot to apply
            success = await self.linkedin_bot.apply_to_job(
                job=job,
                cover_letter=cover_letter,
                custom_message=request.custom_message
            )
            
            # Record application
            application_record = {
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "applied_at": datetime.now().isoformat(),
                "success": success,
                "match_score": job.match_score,
                "cover_letter_generated": bool(cover_letter)
            }
            
            self.application_history.append(application_record)
            self.last_application_time = datetime.now()
            
            if success:
                logger.info(f"Successfully applied to {job.title} at {job.company}")
            else:
                logger.warning(f"Failed to apply to {job.title} at {job.company}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying to job: {str(e)}")
            return False
    
    async def _wait_between_applications(self):
        """Wait between applications to avoid detection"""
        
        try:
            # Random delay between min and max
            delay = random.randint(
                settings.APPLICATION_DELAY_MIN,
                settings.APPLICATION_DELAY_MAX
            )
            
            logger.info(f"Waiting {delay} seconds before next application")
            await asyncio.sleep(delay)
            
        except Exception as e:
            logger.error(f"Error in wait: {str(e)}")
    
    async def pause_auto_apply(self):
        """Pause the auto-apply process"""
        
        self.is_running = False
        logger.info("Auto-apply process paused")
    
    async def resume_auto_apply(self):
        """Resume the auto-apply process"""
        
        self.is_running = True
        logger.info("Auto-apply process resumed")
    
    async def stop_auto_apply(self):
        """Stop the auto-apply process completely"""
        
        self.is_running = False
        logger.info("Auto-apply process stopped")
    
    async def get_application_stats(self) -> Dict[str, Any]:
        """Get statistics about applications"""
        
        try:
            total_applications = len(self.application_history)
            successful_applications = len([app for app in self.application_history if app["success"]])
            
            # Today's applications
            today = datetime.now().date()
            todays_applications = [
                app for app in self.application_history
                if datetime.fromisoformat(app["applied_at"]).date() == today
            ]
            
            # Success rate
            success_rate = (successful_applications / total_applications * 100) if total_applications > 0 else 0
            
            # Average match score
            match_scores = [app["match_score"] for app in self.application_history if app["match_score"]]
            avg_match_score = sum(match_scores) / len(match_scores) if match_scores else 0
            
            # Recent applications (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_applications = [
                app for app in self.application_history
                if datetime.fromisoformat(app["applied_at"]) > cutoff_time
            ]
            
            stats = {
                "total_applications": total_applications,
                "successful_applications": successful_applications,
                "success_rate": round(success_rate, 1),
                "applications_today": len(todays_applications),
                "max_applications_per_day": settings.MAX_APPLICATIONS_PER_DAY,
                "remaining_applications_today": max(0, settings.MAX_APPLICATIONS_PER_DAY - len(todays_applications)),
                "average_match_score": round(avg_match_score, 2),
                "is_running": self.is_running,
                "last_application_time": self.last_application_time.isoformat() if self.last_application_time else None,
                "recent_applications": recent_applications[-10:]  # Last 10 applications
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting application stats: {str(e)}")
            return {
                "error": str(e),
                "total_applications": 0,
                "is_running": self.is_running
            }
    
    async def get_application_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get application history"""
        
        try:
            # Sort by applied_at descending
            sorted_history = sorted(
                self.application_history,
                key=lambda x: x["applied_at"],
                reverse=True
            )
            
            return sorted_history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting application history: {str(e)}")
            return []
    
    async def retry_failed_applications(self, max_retries: int = 5) -> Dict[str, Any]:
        """Retry applications that failed"""
        
        try:
            failed_applications = [
                app for app in self.application_history
                if not app["success"]
            ]
            
            if not failed_applications:
                return {"message": "No failed applications to retry", "retried": 0}
            
            retried_count = 0
            success_count = 0
            
            for app in failed_applications[:max_retries]:
                if self.applications_today >= settings.MAX_APPLICATIONS_PER_DAY:
                    break
                
                # Create job object for retry
                job = JobDetails(
                    id=app["job_id"],
                    title=app["job_title"],
                    company=app["company"],
                    location="",  # Not stored in history
                    url="",  # Not stored in history
                    description="",
                    requirements=[],
                    salary_range="",
                    job_type="",
                    experience_level="",
                    posted_date="",
                    match_score=app.get("match_score")
                )
                
                # Retry application
                success = await self.linkedin_bot.apply_to_job(job)
                
                if success:
                    success_count += 1
                    self.applications_today += 1
                    
                    # Update application record
                    app["success"] = True
                    app["retried_at"] = datetime.now().isoformat()
                
                retried_count += 1
                
                # Wait between retries
                await self._wait_between_applications()
            
            return {
                "message": f"Retried {retried_count} applications, {success_count} successful",
                "retried": retried_count,
                "successful": success_count
            }
            
        except Exception as e:
            logger.error(f"Error retrying failed applications: {str(e)}")
            return {"error": str(e)}
    
    async def schedule_auto_apply(
        self,
        request: AutoApplyRequest,
        schedule_time: datetime
    ) -> Dict[str, Any]:
        """Schedule auto-apply to run at a specific time"""
        
        try:
            current_time = datetime.now()
            
            if schedule_time <= current_time:
                return {"error": "Schedule time must be in the future"}
            
            delay_seconds = (schedule_time - current_time).total_seconds()
            
            # Schedule the task
            asyncio.create_task(self._scheduled_auto_apply(request, delay_seconds))
            
            return {
                "message": f"Auto-apply scheduled for {schedule_time.isoformat()}",
                "scheduled_time": schedule_time.isoformat(),
                "delay_seconds": delay_seconds
            }
            
        except Exception as e:
            logger.error(f"Error scheduling auto-apply: {str(e)}")
            return {"error": str(e)}
    
    async def _scheduled_auto_apply(self, request: AutoApplyRequest, delay_seconds: float):
        """Execute scheduled auto-apply after delay"""
        
        try:
            logger.info(f"Waiting {delay_seconds} seconds for scheduled auto-apply")
            await asyncio.sleep(delay_seconds)
            
            logger.info("Starting scheduled auto-apply process")
            await self.start_auto_apply_process(request)
            
        except Exception as e:
            logger.error(f"Error in scheduled auto-apply: {str(e)}")