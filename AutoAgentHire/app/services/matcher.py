"""
AI-powered job matching and scoring service
"""

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from typing import List, Dict, Any, Optional, Tuple

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.config import settings
from app.models.job_schema import JobDetails
from app.services.resume_parser import ResumeParserService
from app.utils.vectorstore import VectorStoreService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class JobMatcherService:
    """Service for matching jobs to user profiles using AI"""
    
    def __init__(self):
        self.resume_parser = ResumeParserService()
        self.vector_store = VectorStoreService()
        self.user_profile = None
        
        if SKLEARN_AVAILABLE and NUMPY_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        else:
            self.tfidf_vectorizer = None
            logger.warning("scikit-learn or numpy not available - some matching features disabled")
        
        if settings.OPENAI_API_KEY and OPENAI_AVAILABLE:
            openai.api_key = settings.OPENAI_API_KEY
    
    async def load_user_profile(self, resume_path: str = None) -> Dict[str, Any]:
        """Load and parse user's resume to create profile"""
        
        try:
            resume_path = resume_path or settings.RESUME_PATH
            
            if not resume_path:
                raise ValueError("Resume path not provided")
            
            logger.info(f"Loading user profile from: {resume_path}")
            
            # Parse resume
            self.user_profile = await self.resume_parser.parse_resume(resume_path)
            
            # Generate profile embeddings
            profile_text = await self._create_profile_text(self.user_profile)
            self.user_profile["embedding"] = await self.vector_store.generate_embedding(profile_text)
            
            logger.info("User profile loaded successfully")
            return self.user_profile
            
        except Exception as e:
            logger.error(f"Error loading user profile: {str(e)}")
            raise
    
    async def match_jobs(self, jobs: List[JobDetails]) -> List[JobDetails]:
        """Match jobs against user profile and calculate scores"""
        
        try:
            if not self.user_profile:
                logger.warning("User profile not loaded, loading default resume")
                await self.load_user_profile()
            
            matched_jobs = []
            
            for job in jobs:
                # Calculate match score
                match_score = await self._calculate_match_score(job)
                
                # Update job with match score
                job.match_score = match_score
                
                # Only include jobs above threshold
                if match_score >= settings.SIMILARITY_THRESHOLD:
                    matched_jobs.append(job)
                    logger.info(f"Job matched: {job.title} at {job.company} (Score: {match_score:.2f})")
            
            return matched_jobs
            
        except Exception as e:
            logger.error(f"Error matching jobs: {str(e)}")
            return jobs  # Return original jobs if matching fails
    
    async def _calculate_match_score(self, job: JobDetails) -> float:
        """Calculate match score between job and user profile"""
        
        try:
            # Create job text for comparison
            job_text = await self._create_job_text(job)
            
            # Method 1: Semantic similarity using embeddings
            semantic_score = await self._calculate_semantic_similarity(job_text)
            
            # Method 2: Skills matching
            skills_score = await self._calculate_skills_match(job)
            
            # Method 3: Experience level matching
            experience_score = await self._calculate_experience_match(job)
            
            # Method 4: Location preference (if applicable)
            location_score = await self._calculate_location_match(job)
            
            # Method 5: AI-powered comprehensive matching
            ai_score = await self._calculate_ai_match_score(job_text)
            
            # Weighted combination of scores
            final_score = (
                semantic_score * 0.3 +
                skills_score * 0.3 +
                experience_score * 0.2 +
                location_score * 0.1 +
                ai_score * 0.1
            )
            
            return min(final_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.warning(f"Error calculating match score: {str(e)}")
            return 0.5  # Default score
    
    async def _calculate_semantic_similarity(self, job_text: str) -> float:
        """Calculate semantic similarity using embeddings"""
        
        try:
            if not self.user_profile.get("embedding"):
                return 0.5
            
            if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
                logger.warning("scikit-learn or numpy not available for similarity calculation")
                return 0.5
            
            # Generate job embedding
            job_embedding = await self.vector_store.generate_embedding(job_text)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(
                [self.user_profile["embedding"]], 
                [job_embedding]
            )[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Error calculating semantic similarity: {str(e)}")
            return 0.5
    
    async def _calculate_skills_match(self, job: JobDetails) -> float:
        """Calculate skills matching score"""
        
        try:
            user_skills = set(skill.lower() for skill in self.user_profile.get("skills", []))
            
            # Extract skills from job requirements and description
            job_skills = set()
            
            # From requirements
            for req in job.requirements:
                job_skills.add(req.lower())
            
            # From description (simple keyword extraction)
            job_text = (job.description + " " + " ".join(job.requirements)).lower()
            common_skills = [
                'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
                'sql', 'postgresql', 'mysql', 'mongodb', 'aws', 'azure', 'docker',
                'kubernetes', 'git', 'linux', 'fastapi', 'django', 'flask'
            ]
            
            for skill in common_skills:
                if skill in job_text:
                    job_skills.add(skill)
            
            if not job_skills:
                return 0.3  # Default if no skills found
            
            # Calculate overlap
            matching_skills = user_skills.intersection(job_skills)
            skills_score = len(matching_skills) / len(job_skills) if job_skills else 0
            
            return min(skills_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating skills match: {str(e)}")
            return 0.3
    
    async def _calculate_experience_match(self, job: JobDetails) -> float:
        """Calculate experience level matching"""
        
        try:
            user_experience_years = len(self.user_profile.get("experience", []))
            
            # Map experience levels to years
            experience_mapping = {
                "entry": 0,
                "associate": 2,
                "mid": 4,
                "senior": 7,
                "executive": 10
            }
            
            job_experience_level = job.experience_level.lower() if job.experience_level else "mid"
            required_years = experience_mapping.get(job_experience_level, 4)
            
            # Calculate score based on experience gap
            if user_experience_years >= required_years:
                return 1.0
            elif user_experience_years >= required_years * 0.7:
                return 0.8
            elif user_experience_years >= required_years * 0.5:
                return 0.6
            else:
                return 0.3
                
        except Exception as e:
            logger.warning(f"Error calculating experience match: {str(e)}")
            return 0.7
    
    async def _calculate_location_match(self, job: JobDetails) -> float:
        """Calculate location preference matching"""
        
        try:
            # This is a simplified implementation
            # In practice, you'd have user location preferences
            
            user_location = self.user_profile.get("personal_info", {}).get("location", "")
            job_location = job.location.lower() if job.location else ""
            
            # Check for remote work
            if "remote" in job_location:
                return 1.0
            
            # Simple string matching for now
            if user_location and user_location.lower() in job_location:
                return 1.0
            
            return 0.5  # Neutral score if no preference
            
        except Exception as e:
            logger.warning(f"Error calculating location match: {str(e)}")
            return 0.5
    
    async def _calculate_ai_match_score(self, job_text: str) -> float:
        """Use AI to calculate comprehensive match score"""
        
        try:
            if not settings.OPENAI_API_KEY or not OPENAI_AVAILABLE:
                return 0.5
            
            user_summary = await self.resume_parser.get_resume_summary(self.user_profile)
            
            prompt = f"""
            Rate how well this job matches this candidate's profile on a scale of 0.0 to 1.0.
            
            Candidate Profile:
            {user_summary}
            
            Job Description:
            {job_text[:1500]}  # Limit to avoid token limits
            
            Consider skills alignment, experience level, and overall fit.
            Return only a number between 0.0 and 1.0.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )
            
            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"AI matching failed: {str(e)}")
            return 0.5
    
    async def _create_profile_text(self, profile: Dict[str, Any]) -> str:
        """Create text representation of user profile for embedding"""
        
        text_parts = []
        
        # Add summary
        if profile.get("summary"):
            text_parts.append(profile["summary"])
        
        # Add skills
        if profile.get("skills"):
            text_parts.append("Skills: " + ", ".join(profile["skills"]))
        
        # Add experience
        for exp in profile.get("experience", []):
            text_parts.append(f"Experience: {exp.get('title', '')} at {exp.get('company', '')}")
            if exp.get("description"):
                text_parts.append(exp["description"])
        
        # Add education
        for edu in profile.get("education", []):
            text_parts.append(f"Education: {edu.get('degree', '')} from {edu.get('institution', '')}")
        
        return " ".join(text_parts)
    
    async def _create_job_text(self, job: JobDetails) -> str:
        """Create text representation of job for matching"""
        
        text_parts = [
            job.title,
            job.company,
            job.description,
            " ".join(job.requirements),
            job.experience_level or "",
            job.job_type or ""
        ]
        
        return " ".join(filter(None, text_parts))
    
    async def get_match_explanation(self, job: JobDetails) -> Dict[str, Any]:
        """Get detailed explanation of why a job matches"""
        
        try:
            if not self.user_profile:
                return {"error": "User profile not loaded"}
            
            job_text = await self._create_job_text(job)
            
            # Calculate individual scores
            semantic_score = await self._calculate_semantic_similarity(job_text)
            skills_score = await self._calculate_skills_match(job)
            experience_score = await self._calculate_experience_match(job)
            location_score = await self._calculate_location_match(job)
            
            # Find matching skills
            user_skills = set(skill.lower() for skill in self.user_profile.get("skills", []))
            job_requirements = set(req.lower() for req in job.requirements)
            matching_skills = list(user_skills.intersection(job_requirements))
            
            explanation = {
                "overall_score": job.match_score,
                "breakdown": {
                    "semantic_similarity": semantic_score,
                    "skills_match": skills_score,
                    "experience_match": experience_score,
                    "location_match": location_score
                },
                "matching_skills": matching_skills,
                "recommendation": self._get_recommendation(job.match_score or 0)
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error getting match explanation: {str(e)}")
            return {"error": str(e)}
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on match score"""
        
        if score >= 0.8:
            return "Excellent match! Highly recommended to apply."
        elif score >= 0.6:
            return "Good match. Consider applying with a tailored cover letter."
        elif score >= 0.4:
            return "Moderate match. Review requirements carefully before applying."
        else:
            return "Low match. Consider developing additional skills before applying."