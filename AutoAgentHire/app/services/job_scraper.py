"""
LinkedIn job scraping service using Selenium/Playwright
"""

import asyncio
import random
from typing import List, Optional, Dict, Any, Union

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
    WebDriverType = webdriver.Chrome
except ImportError:
    SELENIUM_AVAILABLE = False
    WebDriverType = Any

from app.config import settings
from app.models.job_schema import JobDetails
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class JobScraperService:
    """LinkedIn job scraping service"""
    
    def __init__(self):
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available - job scraping will use mock data")
        self.driver = None
        self.is_logged_in = False
        
    def _setup_driver(self) -> WebDriverType:
        """Setup Chrome WebDriver with appropriate options"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not available")
            
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        return webdriver.Chrome(options=chrome_options)
    
    async def _login_to_linkedin(self) -> bool:
        """Login to LinkedIn using credentials from config"""
        try:
            if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
                logger.warning("LinkedIn credentials not provided")
                return False
                
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 10)
            
            # Enter email
            email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.send_keys(settings.LINKEDIN_EMAIL)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(settings.LINKEDIN_PASSWORD)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for redirect to indicate successful login
            await asyncio.sleep(3)
            
            if "feed" in self.driver.current_url or "jobs" in self.driver.current_url:
                self.is_logged_in = True
                logger.info("Successfully logged into LinkedIn")
                return True
            else:
                logger.error("Failed to login to LinkedIn")
                return False
                
        except Exception as e:
            logger.error(f"Error logging into LinkedIn: {str(e)}")
            return False
    
    async def search_jobs(
        self,
        keywords: str,
        location: str = "",
        experience_level: Optional[str] = None,
        job_type: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 20
    ) -> List[JobDetails]:
        """Search for jobs on LinkedIn"""
        
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available, returning mock job data")
            return self._get_mock_jobs(keywords, limit)
        
        jobs = []
        
        try:
            # Setup driver
            self.driver = self._setup_driver()
            
            # Login if credentials are provided
            if settings.LINKEDIN_EMAIL and settings.LINKEDIN_PASSWORD:
                await self._login_to_linkedin()
            
            # Build search URL
            search_url = self._build_search_url(keywords, location, experience_level, job_type, company)
            
            logger.info(f"Searching jobs with URL: {search_url}")
            self.driver.get(search_url)
            
            # Wait for job listings to load
            await asyncio.sleep(3)
            
            # Extract job listings
            jobs = await self._extract_job_listings(limit)
            
            logger.info(f"Found {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            
        finally:
            if self.driver:
                self.driver.quit()
                
        return jobs
    
    def _get_mock_jobs(self, keywords: str, limit: int) -> List[JobDetails]:
        """Return mock job data for testing"""
        mock_jobs = []
        
        for i in range(min(limit, 5)):  # Return up to 5 mock jobs
            job = JobDetails(
                id=f"mock_job_{i+1}",
                title=f"{keywords} Engineer",
                company=f"Tech Company {i+1}",
                location="San Francisco, CA",
                url=f"https://linkedin.com/jobs/view/mock_{i+1}",
                description=f"Exciting opportunity to work as a {keywords} engineer at a leading tech company.",
                requirements=["Python", "FastAPI", "SQL", "Git"],
                salary_range="$80,000 - $120,000",
                job_type="Full-time",
                experience_level="Mid-level",
                posted_date="2 days ago",
                match_score=0.8 - (i * 0.1)  # Decreasing match scores
            )
            mock_jobs.append(job)
        
        logger.info(f"Generated {len(mock_jobs)} mock jobs")
        return mock_jobs
    
    def _build_search_url(
        self,
        keywords: str,
        location: str = "",
        experience_level: Optional[str] = None,
        job_type: Optional[str] = None,
        company: Optional[str] = None
    ) -> str:
        """Build LinkedIn job search URL"""
        
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = []
        
        if keywords:
            params.append(f"keywords={keywords.replace(' ', '%20')}")
        if location:
            params.append(f"location={location.replace(' ', '%20')}")
        if company:
            params.append(f"f_C={company.replace(' ', '%20')}")
            
        # Add experience level filter
        if experience_level:
            exp_mapping = {
                "entry": "1",
                "associate": "2", 
                "mid": "3",
                "senior": "4",
                "executive": "5"
            }
            if experience_level.lower() in exp_mapping:
                params.append(f"f_E={exp_mapping[experience_level.lower()]}")
        
        # Add job type filter
        if job_type:
            type_mapping = {
                "full-time": "F",
                "part-time": "P",
                "contract": "C",
                "temporary": "T",
                "internship": "I"
            }
            if job_type.lower() in type_mapping:
                params.append(f"f_JT={type_mapping[job_type.lower()]}")
        
        return base_url + "&".join(params)
    
    async def _extract_job_listings(self, limit: int) -> List[JobDetails]:
        """Extract job listings from the current page"""
        
        jobs = []
        
        try:
            # Find job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
            
            for i, card in enumerate(job_cards[:limit]):
                if i >= limit:
                    break
                    
                try:
                    job = await self._extract_job_from_card(card)
                    if job:
                        jobs.append(job)
                        
                    # Add random delay to avoid detection
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    logger.warning(f"Error extracting job from card: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting job listings: {str(e)}")
            
        return jobs
    
    async def _extract_job_from_card(self, card) -> Optional[JobDetails]:
        """Extract job details from a job card element"""
        
        try:
            # Extract job ID
            job_id = card.get_attribute("data-job-id")
            
            # Extract title
            title_element = card.find_element(By.CSS_SELECTOR, "h3, .job-card-list__title")
            title = title_element.text.strip()
            
            # Extract company
            company_element = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name, h4")
            company = company_element.text.strip()
            
            # Extract location
            location_element = card.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-item")
            location = location_element.text.strip()
            
            # Extract job URL
            link_element = card.find_element(By.CSS_SELECTOR, "a")
            job_url = link_element.get_attribute("href")
            
            # Create job details object
            job = JobDetails(
                id=job_id,
                title=title,
                company=company,
                location=location,
                url=job_url,
                description="",  # Will be filled by get_job_details if needed
                requirements=[],
                salary_range="",
                job_type="",
                experience_level="",
                posted_date="",
                match_score=None
            )
            
            return job
            
        except Exception as e:
            logger.warning(f"Error extracting job details: {str(e)}")
            return None
    
    async def get_job_details(self, job_id: str) -> Optional[JobDetails]:
        """Get detailed information about a specific job"""
        
        try:
            if not SELENIUM_AVAILABLE:
                return None
                
            # This is a placeholder implementation
            # In a real implementation, you would navigate to the job detail page
            # and extract comprehensive information
            
            logger.info(f"Getting details for job ID: {job_id}")
            
            # Mock job details for now
            job_details = JobDetails(
                id=job_id,
                title="Software Engineer",
                company="Example Company",
                location="San Francisco, CA",
                url=f"https://www.linkedin.com/jobs/view/{job_id}",
                description="This is a sample job description that would be extracted from the job detail page.",
                requirements=["Python", "FastAPI", "SQL", "Git"],
                salary_range="$80,000 - $120,000",
                job_type="Full-time",
                experience_level="Mid-level",
                posted_date="2 days ago",
                match_score=None
            )
            
            return job_details
            
        except Exception as e:
            logger.error(f"Error getting job details: {str(e)}")
            return None