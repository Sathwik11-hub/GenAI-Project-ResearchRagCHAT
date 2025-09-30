"""
NLP-based resume parsing service
"""

import os
import re
from typing import Dict, List, Any, Optional
from io import BytesIO

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ResumeParserService:
    """Service for parsing and extracting information from resumes"""
    
    def __init__(self):
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 not available - resume parsing will use mock data")
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available - AI enhancements disabled")
        if settings.OPENAI_API_KEY and OPENAI_AVAILABLE:
            openai.api_key = settings.OPENAI_API_KEY
    
    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse a resume file and extract structured information"""
        
        try:
            # Extract text from PDF
            text = await self._extract_text_from_pdf(file_path)
            
            if not text:
                raise ValueError("Could not extract text from resume")
            
            # Parse the extracted text
            parsed_data = await self._parse_resume_text(text)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file"""
        
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 not available, returning mock resume text")
            return "John Doe\njohn.doe@email.com\n(555) 123-4567\n\nExperienced Software Engineer with 5 years in Python development, FastAPI, and SQL."
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    async def _parse_resume_text(self, text: str) -> Dict[str, Any]:
        """Parse resume text and extract structured information"""
        
        # Initialize parsed data structure
        parsed_data = {
            "personal_info": {},
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "projects": []
        }
        
        try:
            # Extract personal information
            parsed_data["personal_info"] = self._extract_personal_info(text)
            
            # Extract skills
            parsed_data["skills"] = self._extract_skills(text)
            
            # Extract work experience
            parsed_data["experience"] = self._extract_experience(text)
            
            # Extract education
            parsed_data["education"] = self._extract_education(text)
            
            # Extract summary/objective
            parsed_data["summary"] = self._extract_summary(text)
            
            # Use OpenAI for advanced parsing if API key is available
            if settings.OPENAI_API_KEY and OPENAI_AVAILABLE:
                enhanced_data = await self._enhance_parsing_with_ai(text)
                parsed_data.update(enhanced_data)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume text: {str(e)}")
            return parsed_data
    
    def _extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information like name, email, phone"""
        
        personal_info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            personal_info["email"] = email_match.group()
        
        # Extract phone number
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            personal_info["phone"] = phone_match.group()
        
        # Extract name (usually the first line or largest text)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line.split()) <= 4:  # Name usually 1-4 words
                personal_info["name"] = line
                break
        
        return personal_info
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        
        skills = []
        
        # Common technical skills
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'aws', 'azure',
            'docker', 'kubernetes', 'git', 'linux', 'fastapi', 'django', 'flask',
            'machine learning', 'ai', 'nlp', 'data science', 'tensorflow', 'pytorch',
            'html', 'css', 'typescript', 'c++', 'c#', 'go', 'rust', 'scala'
        ]
        
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill in text_lower:
                skills.append(skill.title())
        
        # Look for skills sections
        skills_patterns = [
            r'skills?[:\-\s]*(.*?)(?=\n\s*\n|\n[A-Z]|\Z)',
            r'technical skills?[:\-\s]*(.*?)(?=\n\s*\n|\n[A-Z]|\Z)',
            r'technologies?[:\-\s]*(.*?)(?=\n\s*\n|\n[A-Z]|\Z)'
        ]
        
        for pattern in skills_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                skills_text = match.group(1)
                # Extract skills from bullet points or comma-separated lists
                skill_items = re.findall(r'[•\-\*]?\s*([A-Za-z0-9+#\.\s]+)', skills_text)
                skills.extend([skill.strip() for skill in skill_items if skill.strip()])
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience from resume text"""
        
        experience = []
        
        # Look for experience sections
        exp_patterns = [
            r'experience[:\-\s]*(.*?)(?=education|skills|projects|certifications|\Z)',
            r'work experience[:\-\s]*(.*?)(?=education|skills|projects|certifications|\Z)',
            r'employment[:\-\s]*(.*?)(?=education|skills|projects|certifications|\Z)'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                exp_text = match.group(1)
                
                # Simple extraction - in practice, this would be more sophisticated
                job_entries = re.split(r'\n\s*\n', exp_text)
                
                for entry in job_entries:
                    if entry.strip():
                        lines = entry.strip().split('\n')
                        if len(lines) >= 2:
                            experience.append({
                                "title": lines[0].strip(),
                                "company": lines[1].strip() if len(lines) > 1 else "",
                                "duration": "",
                                "description": entry.strip()
                            })
                break
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from resume text"""
        
        education = []
        
        # Look for education sections
        edu_patterns = [
            r'education[:\-\s]*(.*?)(?=experience|skills|projects|certifications|\Z)',
            r'academic background[:\-\s]*(.*?)(?=experience|skills|projects|certifications|\Z)'
        ]
        
        for pattern in edu_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                edu_text = match.group(1)
                
                # Extract degree information
                degree_patterns = [
                    r'(bachelor|master|phd|doctorate|bs|ms|ba|ma|mba|btech|mtech)',
                    r'(university|college|institute)',
                    r'(\d{4})'  # Graduation year
                ]
                
                education.append({
                    "degree": edu_text.strip(),
                    "institution": "",
                    "year": "",
                    "details": edu_text.strip()
                })
                break
        
        return education
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary or objective"""
        
        summary_patterns = [
            r'summary[:\-\s]*(.*?)(?=\n\s*\n|\n[A-Z])',
            r'objective[:\-\s]*(.*?)(?=\n\s*\n|\n[A-Z])',
            r'professional summary[:\-\s]*(.*?)(?=\n\s*\n|\n[A-Z])',
            r'career objective[:\-\s]*(.*?)(?=\n\s*\n|\n[A-Z])'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    async def _enhance_parsing_with_ai(self, text: str) -> Dict[str, Any]:
        """Use OpenAI to enhance resume parsing"""
        
        try:
            prompt = f"""
            Parse the following resume text and extract structured information in JSON format.
            Include: personal_info (name, email, phone), skills, experience, education, summary.
            
            Resume text:
            {text[:3000]}  # Limit text to avoid token limits
            
            Return only valid JSON.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0
            )
            
            # Parse the response
            import json
            enhanced_data = json.loads(response.choices[0].message.content)
            
            return enhanced_data
            
        except Exception as e:
            logger.warning(f"AI enhancement failed: {str(e)}")
            return {}
    
    async def get_resume_summary(self, parsed_resume: Dict[str, Any]) -> str:
        """Generate a summary of the parsed resume for job matching"""
        
        summary_parts = []
        
        # Add skills
        if parsed_resume.get("skills"):
            skills_text = ", ".join(parsed_resume["skills"][:10])  # Top 10 skills
            summary_parts.append(f"Skills: {skills_text}")
        
        # Add experience
        if parsed_resume.get("experience"):
            exp_count = len(parsed_resume["experience"])
            summary_parts.append(f"Experience: {exp_count} positions")
        
        # Add education
        if parsed_resume.get("education"):
            education = parsed_resume["education"][0] if parsed_resume["education"] else {}
            if education.get("degree"):
                summary_parts.append(f"Education: {education['degree']}")
        
        # Add professional summary
        if parsed_resume.get("summary"):
            summary_parts.append(f"Summary: {parsed_resume['summary'][:200]}")
        
        return " | ".join(summary_parts)