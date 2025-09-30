"""
LLM-based cover letter generation service
"""

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from typing import Dict, Any, Optional
from datetime import datetime
import os

from app.config import settings
from app.models.job_schema import JobDetails
from app.services.resume_parser import ResumeParserService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class CoverLetterGeneratorService:
    """Service for generating personalized cover letters using LLM"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY and OPENAI_AVAILABLE:
            openai.api_key = settings.OPENAI_API_KEY
        elif not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available - cover letter generation will use templates only")
        
        self.resume_parser = ResumeParserService()
        self.user_profile = None
    
    async def generate_cover_letter(
        self,
        job: JobDetails,
        user_profile: Dict[str, Any] = None,
        template_path: str = None,
        tone: str = "professional"
    ) -> str:
        """Generate a personalized cover letter for a specific job"""
        
        try:
            # Load user profile if not provided
            if not user_profile:
                if not self.user_profile:
                    logger.info("Loading user profile for cover letter generation")
                    self.user_profile = await self.resume_parser.parse_resume(settings.RESUME_PATH)
                user_profile = self.user_profile
            
            # Load template if provided
            template = await self._load_template(template_path)
            
            # Generate cover letter using AI
            cover_letter = await self._generate_with_ai(job, user_profile, template, tone)
            
            logger.info(f"Generated cover letter for {job.title} at {job.company}")
            return cover_letter
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return await self._generate_fallback_cover_letter(job, user_profile)
    
    async def _load_template(self, template_path: str = None) -> str:
        """Load cover letter template from file"""
        
        try:
            template_path = template_path or settings.COVER_LETTER_TEMPLATE_PATH
            
            if template_path and os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                return self._get_default_template()
                
        except Exception as e:
            logger.warning(f"Error loading template: {str(e)}")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Get default cover letter template"""
        
        return """
Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. With my background in {relevant_skills} and {years_experience} years of experience in {field}, I am confident that I would be a valuable addition to your team.

In my previous roles, I have:
{key_achievements}

I am particularly drawn to this opportunity because:
{why_interested}

I am excited about the possibility of contributing to {company_name}'s continued success and would welcome the opportunity to discuss how my skills and experience align with your needs.

Thank you for your time and consideration.

Sincerely,
{candidate_name}
        """.strip()
    
    async def _generate_with_ai(
        self,
        job: JobDetails,
        user_profile: Dict[str, Any],
        template: str,
        tone: str
    ) -> str:
        """Generate cover letter using OpenAI"""
        
        try:
            if not settings.OPENAI_API_KEY or not OPENAI_AVAILABLE:
                return await self._generate_template_based(job, user_profile, template)
            
            # Prepare context for AI
            user_summary = await self._create_user_summary(user_profile)
            job_summary = await self._create_job_summary(job)
            
            prompt = self._create_ai_prompt(user_summary, job_summary, tone)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional career counselor who writes compelling, personalized cover letters."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            cover_letter = response.choices[0].message.content.strip()
            
            # Post-process the cover letter
            cover_letter = await self._post_process_cover_letter(cover_letter, job, user_profile)
            
            return cover_letter
            
        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            return await self._generate_template_based(job, user_profile, template)
    
    def _create_ai_prompt(self, user_summary: str, job_summary: str, tone: str) -> str:
        """Create prompt for AI cover letter generation"""
        
        prompt = f"""
Write a compelling cover letter for the following job application.

CANDIDATE PROFILE:
{user_summary}

JOB DETAILS:
{job_summary}

REQUIREMENTS:
- Tone: {tone}
- Length: 3-4 paragraphs
- Highlight relevant skills and experience
- Show enthusiasm for the role and company
- Include specific examples when possible
- Professional format with proper greeting and closing
- Avoid generic phrases
- Make it personalized and engaging

Generate a complete cover letter that would make this candidate stand out.
        """
        
        return prompt
    
    async def _create_user_summary(self, user_profile: Dict[str, Any]) -> str:
        """Create a summary of the user's profile for AI prompt"""
        
        summary_parts = []
        
        # Personal info
        personal_info = user_profile.get("personal_info", {})
        if personal_info.get("name"):
            summary_parts.append(f"Name: {personal_info['name']}")
        
        # Professional summary
        if user_profile.get("summary"):
            summary_parts.append(f"Professional Summary: {user_profile['summary']}")
        
        # Skills
        if user_profile.get("skills"):
            skills_text = ", ".join(user_profile["skills"][:15])  # Top 15 skills
            summary_parts.append(f"Key Skills: {skills_text}")
        
        # Experience
        for i, exp in enumerate(user_profile.get("experience", [])[:3]):  # Top 3 experiences
            exp_text = f"Experience {i+1}: {exp.get('title', '')} at {exp.get('company', '')}"
            if exp.get("description"):
                exp_text += f" - {exp['description'][:200]}"
            summary_parts.append(exp_text)
        
        # Education
        if user_profile.get("education"):
            edu = user_profile["education"][0]  # Most recent education
            edu_text = f"Education: {edu.get('degree', '')} from {edu.get('institution', '')}"
            summary_parts.append(edu_text)
        
        return "\n".join(summary_parts)
    
    async def _create_job_summary(self, job: JobDetails) -> str:
        """Create a summary of the job for AI prompt"""
        
        summary_parts = [
            f"Job Title: {job.title}",
            f"Company: {job.company}",
            f"Location: {job.location}"
        ]
        
        if job.description:
            summary_parts.append(f"Description: {job.description[:500]}")
        
        if job.requirements:
            req_text = ", ".join(job.requirements[:10])  # Top 10 requirements
            summary_parts.append(f"Requirements: {req_text}")
        
        if job.experience_level:
            summary_parts.append(f"Experience Level: {job.experience_level}")
        
        if job.job_type:
            summary_parts.append(f"Job Type: {job.job_type}")
        
        return "\n".join(summary_parts)
    
    async def _generate_template_based(
        self,
        job: JobDetails,
        user_profile: Dict[str, Any],
        template: str
    ) -> str:
        """Generate cover letter using template substitution"""
        
        try:
            # Extract variables for template
            personal_info = user_profile.get("personal_info", {})
            candidate_name = personal_info.get("name", "")
            
            # Calculate years of experience
            years_experience = len(user_profile.get("experience", []))
            
            # Get relevant skills
            relevant_skills = ", ".join(user_profile.get("skills", [])[:5])
            
            # Determine field from experience
            field = "technology"  # Default
            if user_profile.get("experience"):
                first_exp = user_profile["experience"][0]
                if first_exp.get("title"):
                    title = first_exp["title"].lower()
                    if "engineer" in title or "developer" in title:
                        field = "software development"
                    elif "manager" in title:
                        field = "management"
                    elif "analyst" in title:
                        field = "analysis"
            
            # Create key achievements
            key_achievements = []
            for exp in user_profile.get("experience", [])[:2]:
                if exp.get("title") and exp.get("company"):
                    key_achievements.append(f"• {exp['title']} at {exp['company']}")
            key_achievements_text = "\n".join(key_achievements) if key_achievements else "• Developed strong technical and professional skills"
            
            # Why interested (generic but tailored)
            why_interested = f"The opportunity to contribute to {job.company}'s mission aligns perfectly with my career goals and expertise in {relevant_skills.split(',')[0] if relevant_skills else 'technology'}."
            
            # Fill template
            cover_letter = template.format(
                job_title=job.title,
                company_name=job.company,
                relevant_skills=relevant_skills,
                years_experience=years_experience,
                field=field,
                key_achievements=key_achievements_text,
                why_interested=why_interested,
                candidate_name=candidate_name
            )
            
            return cover_letter
            
        except Exception as e:
            logger.error(f"Template generation failed: {str(e)}")
            return await self._generate_fallback_cover_letter(job, user_profile)
    
    async def _post_process_cover_letter(
        self,
        cover_letter: str,
        job: JobDetails,
        user_profile: Dict[str, Any]
    ) -> str:
        """Post-process the generated cover letter"""
        
        try:
            # Add date
            date_str = datetime.now().strftime("%B %d, %Y")
            
            # Format the cover letter
            processed_letter = f"""
{date_str}

{job.company} Hiring Team
{job.location}

{cover_letter}
            """.strip()
            
            return processed_letter
            
        except Exception as e:
            logger.warning(f"Post-processing failed: {str(e)}")
            return cover_letter
    
    async def _generate_fallback_cover_letter(
        self,
        job: JobDetails,
        user_profile: Dict[str, Any]
    ) -> str:
        """Generate a basic fallback cover letter"""
        
        candidate_name = user_profile.get("personal_info", {}).get("name", "")
        skills = ", ".join(user_profile.get("skills", [])[:3])
        
        return f"""
Dear {job.company} Hiring Team,

I am writing to express my interest in the {job.title} position at {job.company}. 

With my background in {skills} and proven experience in the field, I am confident that I would be a valuable addition to your team. I am particularly excited about the opportunity to contribute to {job.company}'s continued success.

I would welcome the opportunity to discuss how my skills and experience align with your needs.

Thank you for your consideration.

Sincerely,
{candidate_name}
        """.strip()
    
    async def customize_cover_letter(
        self,
        base_cover_letter: str,
        customizations: Dict[str, str]
    ) -> str:
        """Apply customizations to a base cover letter"""
        
        try:
            customized_letter = base_cover_letter
            
            for placeholder, value in customizations.items():
                customized_letter = customized_letter.replace(f"{{{placeholder}}}", value)
            
            return customized_letter
            
        except Exception as e:
            logger.error(f"Error customizing cover letter: {str(e)}")
            return base_cover_letter
    
    async def validate_cover_letter(self, cover_letter: str) -> Dict[str, Any]:
        """Validate and provide feedback on cover letter quality"""
        
        validation_results = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
            "score": 0.0
        }
        
        try:
            # Check length
            word_count = len(cover_letter.split())
            if word_count < 150:
                validation_results["issues"].append("Cover letter is too short")
                validation_results["suggestions"].append("Add more details about your experience and interest")
            elif word_count > 500:
                validation_results["issues"].append("Cover letter is too long")
                validation_results["suggestions"].append("Condense to 3-4 paragraphs")
            
            # Check for placeholders
            if "{" in cover_letter and "}" in cover_letter:
                validation_results["issues"].append("Contains unfilled placeholders")
                validation_results["is_valid"] = False
            
            # Check for generic content
            generic_phrases = ["to whom it may concern", "dear sir/madam", "i am writing to apply"]
            for phrase in generic_phrases:
                if phrase in cover_letter.lower():
                    validation_results["suggestions"].append(f"Consider making the greeting more specific")
                    break
            
            # Calculate basic score
            score = 1.0
            score -= len(validation_results["issues"]) * 0.2
            score -= len(validation_results["suggestions"]) * 0.1
            validation_results["score"] = max(0.0, score)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating cover letter: {str(e)}")
            validation_results["issues"].append("Validation failed")
            validation_results["is_valid"] = False
            return validation_results