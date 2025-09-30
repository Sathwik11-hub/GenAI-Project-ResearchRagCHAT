"""
LinkedIn automation bot using Selenium/Playwright
"""

import asyncio
import random
from typing import Optional, Dict, Any

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
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

class LinkedInBot:
    """LinkedIn automation bot for job applications"""
    
    def __init__(self):
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available - LinkedIn automation will be disabled")
        self.driver = None
        self.is_logged_in = False
        self.wait = None
        
    def _setup_driver(self) -> WebDriverType:
        """Setup Chrome WebDriver with stealth options"""
        
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not available")
        
        chrome_options = Options()
        
        # Stealth options to avoid detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Run in headless mode for production
        if not settings.DEBUG:
            chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to hide automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    async def login(self) -> bool:
        """Login to LinkedIn using credentials"""
        
        try:
            if not SELENIUM_AVAILABLE:
                logger.warning("Selenium not available - cannot login to LinkedIn")
                return False
                
            if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
                logger.error("LinkedIn credentials not provided in settings")
                return False
            
            self.driver = self._setup_driver()
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("Navigating to LinkedIn login page")
            self.driver.get("https://www.linkedin.com/login")
            
            # Random delay to mimic human behavior
            await asyncio.sleep(random.uniform(2, 4))
            
            # Enter email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            await self._human_type(email_field, settings.LINKEDIN_EMAIL)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            await self._human_type(password_field, settings.LINKEDIN_PASSWORD)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            await asyncio.sleep(random.uniform(3, 5))
            
            # Check if login was successful
            if self._is_login_successful():
                self.is_logged_in = True
                logger.info("Successfully logged into LinkedIn")
                return True
            else:
                logger.error("LinkedIn login failed - check credentials or CAPTCHA")
                return False
                
        except Exception as e:
            logger.error(f"Error during LinkedIn login: {str(e)}")
            return False
    
    def _is_login_successful(self) -> bool:
        """Check if login was successful"""
        
        try:
            current_url = self.driver.current_url
            
            # Check for successful login indicators
            success_indicators = [
                "linkedin.com/feed",
                "linkedin.com/jobs",
                "linkedin.com/in/",
                "linkedin.com/messaging"
            ]
            
            return any(indicator in current_url for indicator in success_indicators)
            
        except Exception:
            return False
    
    async def apply_to_job(
        self, 
        job: JobDetails, 
        cover_letter: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> bool:
        """Apply to a specific job"""
        
        try:
            if not SELENIUM_AVAILABLE:
                logger.warning("Selenium not available - simulating job application")
                await asyncio.sleep(2)  # Simulate processing time
                return True  # Mock success for testing
            
            if not self.is_logged_in:
                logger.warning("Not logged in to LinkedIn, attempting login")
                if not await self.login():
                    return False
            
            logger.info(f"Applying to job: {job.title} at {job.company}")
            
            # Navigate to job posting
            self.driver.get(job.url)
            await asyncio.sleep(random.uniform(2, 4))
            
            # Find and click Apply button
            if not await self._click_apply_button():
                logger.warning("Could not find Apply button")
                return False
            
            # Handle application process
            success = await self._handle_application_process(job, cover_letter, custom_message)
            
            if success:
                logger.info(f"Successfully applied to {job.title} at {job.company}")
            else:
                logger.warning(f"Failed to complete application for {job.title} at {job.company}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying to job: {str(e)}")
            return False
    
    async def _click_apply_button(self) -> bool:
        """Find and click the Apply button"""
        
        try:
            # Try different selectors for Apply button
            apply_selectors = [
                "//button[contains(@class, 'jobs-apply-button')]",
                "//button[contains(text(), 'Apply')]",
                "//a[contains(@class, 'jobs-apply-button')]",
                "//button[contains(@aria-label, 'Apply')]",
                ".jobs-apply-button",
                ".jobs-s-apply"
            ]
            
            for selector in apply_selectors:
                try:
                    if selector.startswith("//"):
                        apply_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if apply_button.is_enabled():
                        apply_button.click()
                        await asyncio.sleep(random.uniform(1, 2))
                        return True
                        
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error clicking apply button: {str(e)}")
            return False
    
    async def _handle_application_process(
        self, 
        job: JobDetails, 
        cover_letter: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> bool:
        """Handle the multi-step application process"""
        
        try:
            max_steps = 5  # Maximum number of application steps
            current_step = 0
            
            while current_step < max_steps:
                current_step += 1
                
                # Wait for page to load
                await asyncio.sleep(random.uniform(2, 3))
                
                # Check if we're on application form
                if await self._handle_application_form(cover_letter, custom_message):
                    continue
                
                # Check if we need to answer questions
                if await self._handle_application_questions():
                    continue
                
                # Check if we can submit application
                if await self._submit_application():
                    return True
                
                # Check if application is already submitted
                if self._is_application_submitted():
                    return True
                
                # Check for next button
                if await self._click_next_button():
                    continue
                
                # If none of the above worked, we might be done or stuck
                break
            
            logger.warning("Reached maximum application steps without completion")
            return False
            
        except Exception as e:
            logger.error(f"Error in application process: {str(e)}")
            return False
    
    async def _handle_application_form(
        self, 
        cover_letter: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> bool:
        """Handle application form fields"""
        
        try:
            form_handled = False
            
            # Handle cover letter field
            if cover_letter:
                cover_letter_fields = [
                    "//textarea[contains(@name, 'cover')]",
                    "//textarea[contains(@id, 'cover')]",
                    "//textarea[contains(@placeholder, 'cover')]"
                ]
                
                for selector in cover_letter_fields:
                    try:
                        field = self.driver.find_element(By.XPATH, selector)
                        await self._human_type(field, cover_letter)
                        form_handled = True
                        break
                    except NoSuchElementException:
                        continue
            
            # Handle custom message field
            if custom_message:
                message_fields = [
                    "//textarea[contains(@name, 'message')]",
                    "//textarea[contains(@id, 'message')]",
                    "//textarea[contains(@placeholder, 'message')]"
                ]
                
                for selector in message_fields:
                    try:
                        field = self.driver.find_element(By.XPATH, selector)
                        await self._human_type(field, custom_message)
                        form_handled = True
                        break
                    except NoSuchElementException:
                        continue
            
            return form_handled
            
        except Exception as e:
            logger.error(f"Error handling application form: {str(e)}")
            return False
    
    async def _handle_application_questions(self) -> bool:
        """Handle application screening questions"""
        
        try:
            questions_handled = False
            
            # Look for radio buttons (Yes/No questions)
            radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            
            for radio in radio_buttons:
                try:
                    # Get the label text
                    label = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        f"label[for='{radio.get_attribute('id')}']"
                    )
                    label_text = label.text.lower()
                    
                    # Simple logic for common questions
                    if "authorized to work" in label_text and "yes" in label_text:
                        radio.click()
                        questions_handled = True
                    elif "require sponsorship" in label_text and "no" in label_text:
                        radio.click()
                        questions_handled = True
                    elif "experience" in label_text and "yes" in label_text:
                        radio.click()
                        questions_handled = True
                        
                except Exception:
                    continue
            
            # Handle dropdown questions
            dropdowns = self.driver.find_elements(By.CSS_SELECTOR, "select")
            
            for dropdown in dropdowns:
                try:
                    options = dropdown.find_elements(By.TAG_NAME, "option")
                    if len(options) > 1:  # Skip if only one option
                        # Select the first non-empty option
                        for option in options[1:]:
                            if option.text.strip():
                                option.click()
                                questions_handled = True
                                break
                except Exception:
                    continue
            
            return questions_handled
            
        except Exception as e:
            logger.error(f"Error handling application questions: {str(e)}")
            return False
    
    async def _submit_application(self) -> bool:
        """Submit the application"""
        
        try:
            submit_selectors = [
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Submit application')]",
                "//button[contains(@aria-label, 'Submit')]",
                ".jobs-apply-form__submit-button",
                "input[type='submit']"
            ]
            
            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        submit_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if submit_button.is_enabled():
                        submit_button.click()
                        await asyncio.sleep(random.uniform(2, 4))
                        return True
                        
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error submitting application: {str(e)}")
            return False
    
    async def _click_next_button(self) -> bool:
        """Click next button if available"""
        
        try:
            next_selectors = [
                "//button[contains(text(), 'Next')]",
                "//button[contains(text(), 'Continue')]",
                "//button[contains(@aria-label, 'Next')]",
                ".jobs-apply-form__next-button"
            ]
            
            for selector in next_selectors:
                try:
                    if selector.startswith("//"):
                        next_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if next_button.is_enabled():
                        next_button.click()
                        await asyncio.sleep(random.uniform(1, 2))
                        return True
                        
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error clicking next button: {str(e)}")
            return False
    
    def _is_application_submitted(self) -> bool:
        """Check if application has been submitted"""
        
        try:
            success_indicators = [
                "application submitted",
                "application sent", 
                "thank you for applying",
                "your application has been received"
            ]
            
            page_text = self.driver.page_source.lower()
            return any(indicator in page_text for indicator in success_indicators)
            
        except Exception:
            return False
    
    async def _human_type(self, element, text: str):
        """Type text in a human-like manner"""
        
        try:
            element.clear()
            
            for char in text:
                element.send_keys(char)
                # Random delay between keystrokes
                await asyncio.sleep(random.uniform(0.05, 0.15))
                
        except Exception as e:
            logger.error(f"Error typing text: {str(e)}")
    
    async def search_and_apply_jobs(
        self,
        keywords: str,
        location: str = "",
        max_applications: int = 5
    ) -> Dict[str, Any]:
        """Search for jobs and apply automatically"""
        
        try:
            if not self.is_logged_in:
                if not await self.login():
                    return {"success": False, "message": "Login failed"}
            
            # Navigate to jobs page
            self.driver.get("https://www.linkedin.com/jobs/")
            await asyncio.sleep(random.uniform(2, 4))
            
            # Search for jobs
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label*='Search']"))
            )
            
            await self._human_type(search_box, keywords)
            search_box.send_keys(Keys.RETURN)
            
            await asyncio.sleep(random.uniform(3, 5))
            
            # Apply to jobs
            applications_sent = 0
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".jobs-search-results__list-item"
            )
            
            for card in job_cards[:max_applications * 2]:  # Get more cards than needed
                try:
                    if applications_sent >= max_applications:
                        break
                    
                    # Click on job card
                    card.click()
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    # Try to apply
                    if await self._click_apply_button():
                        # Create mock job object
                        job_title = card.find_element(
                            By.CSS_SELECTOR, 
                            ".job-card-list__title"
                        ).text
                        
                        mock_job = JobDetails(
                            id=f"linkedin_{applications_sent}",
                            title=job_title,
                            company="LinkedIn Company",
                            location=location,
                            url=self.driver.current_url,
                            description="",
                            requirements=[],
                            salary_range="",
                            job_type="",
                            experience_level="",
                            posted_date=""
                        )
                        
                        success = await self._handle_application_process(mock_job)
                        if success:
                            applications_sent += 1
                            logger.info(f"Applied to job {applications_sent}: {job_title}")
                    
                    # Random delay between applications
                    await asyncio.sleep(random.uniform(10, 20))
                    
                except Exception as e:
                    logger.warning(f"Error processing job card: {str(e)}")
                    continue
            
            return {
                "success": True,
                "applications_sent": applications_sent,
                "message": f"Successfully sent {applications_sent} applications"
            }
            
        except Exception as e:
            logger.error(f"Error in search and apply: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def close(self):
        """Close the browser and cleanup"""
        
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.is_logged_in = False
                logger.info("LinkedIn bot closed")
                
        except Exception as e:
            logger.error(f"Error closing LinkedIn bot: {str(e)}")
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close()