from tools.pipeline import (
    extract_resume_data,
    match_similar_resumes,
    enhance_resume,
    recommend_career_paths,
    fetch_recommended_courses,
    generate_cover_letter,
    generate_interview_questions,
    clean_llm_output
)
from tools.course_fetcher import fetch_intelligent_courses
from tools.local_llm import call_local_llm_api
from crewai import Tool
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_llm_fallback(role: str, prompt: str, max_tokens: int = 700, context: str = ""):
    """Handle LLM fallback when API fails, with context for better local responses."""
    try:
        # Try local LLM as fallback
        logger.info(f"🔄 Using local LLM fallback for: {context}")
        local_response = call_local_llm_api(role, prompt, max_tokens)
        
        if not local_response.startswith("❌"):
            logger.info(f"✅ Local LLM fallback successful for: {context}")
            return local_response
        else:
            logger.error(f"❌ Local LLM fallback failed for: {context}")
            return f"⚠️ Service temporarily unavailable. Please try again later. (Local fallback failed: {local_response})"
            
    except Exception as e:
        logger.error(f"❌ Local LLM fallback exception for {context}: {str(e)}")
        return f"⚠️ Service temporarily unavailable. Please try again later."

# Wrapper functions to ensure cleaning is applied
def clean_extract_resume_data(resume_text: str, filename: str):
    """Wrapper for extract_resume_data with cleaning applied."""
    try:
        result = extract_resume_data(resume_text, filename)
        # Clean the experience field if it's a string
        if isinstance(result, dict) and 'experience' in result:
            if isinstance(result['experience'], str):
                result['experience'] = clean_llm_output(result['experience'])
        return result
    except Exception as e:
        logger.error(f"❌ Resume extraction failed: {str(e)}")
        return {
            "skills": ["Error extracting skills"],
            "experience": "Error extracting experience"
        }

def clean_match_similar_resumes(query_text: str, filename: str, top_k: int = 3):
    """Wrapper for LLM-powered resume matching with cleaning and fallback."""
    try:
        result = match_similar_resumes(query_text, filename, top_k)
        return clean_llm_output(result)
    except Exception as e:
        logger.error(f"❌ LLM-powered resume matching failed: {str(e)}")
        # Fallback: use basic FAISS similarity links
        try:
            from tools.faiss_utils import FaissHandler
            handler = FaissHandler()
            matches = handler.search_with_clickable_links(query_text, "resume", top_k, exclude_filename=filename)
            return f"⚠️ LLM analysis failed, showing basic similarity results:\n\n{matches}"
        except Exception as fallback_error:
            return f"📝 Resume matching service temporarily unavailable. Error: {str(fallback_error)}"

def clean_enhance_resume(resume_text: str, target_job_role: str):
    """Wrapper for enhance_resume with cleaning applied."""
    try:
        result = enhance_resume(resume_text, target_job_role)
        return clean_llm_output(result)
    except Exception as e:
        logger.error(f"❌ Resume enhancement failed: {str(e)}")
        # Try local fallback for resume enhancement
        fallback_prompt = f"Enhance this resume for the role of {target_job_role}. Add a professional summary and improve formatting:\n\n{resume_text}"
        return handle_llm_fallback("You are a professional resume editor.", fallback_prompt, 1200, "resume enhancement")

def clean_recommend_career_paths(resume_text: str):
    """Wrapper for recommend_career_paths with cleaning applied."""
    try:
        result = recommend_career_paths(resume_text)
        return clean_llm_output(result)
    except Exception as e:
        logger.error(f"❌ Career path recommendation failed: {str(e)}")
        # Try local fallback for career recommendations
        fallback_prompt = f"Suggest 3 job roles based on this resume:\n\n{resume_text}"
        return handle_llm_fallback("You are a career strategist.", fallback_prompt, 700, "career recommendations")

def clean_fetch_intelligent_courses(resume_text: str):
    """Wrapper for intelligent course fetching with enhanced error handling."""
    try:
        # Use the new intelligent course fetching system
        result = fetch_intelligent_courses(resume_text, max_results=5)
        return clean_llm_output(result)
    except Exception as e:
        logger.error(f"❌ Intelligent course recommendation failed: {str(e)}")
        # Try local fallback for course recommendations
        fallback_prompt = f"""
        Based on this resume, suggest 3-5 online courses that would be most beneficial:
        
        Resume: {resume_text}
        
        Provide recommendations in this format:
        - Course Title (Platform)
        - Why it's relevant
        - Skill level (Beginner/Intermediate/Advanced)
        """
        return handle_llm_fallback("You are an expert learning advisor.", fallback_prompt, 800, "intelligent course recommendations")

def clean_generate_cover_letter(resume_text: str):
    """Wrapper for generate_cover_letter with cleaning applied."""
    try:
        result = generate_cover_letter(resume_text)
        return clean_llm_output(result)
    except Exception as e:
        logger.error(f"❌ Cover letter generation failed: {str(e)}")
        # Try local fallback for cover letter generation
        fallback_prompt = (
            "Write a professional cover letter for a job application based on the following resume. "
            "The letter should be in standard business letter format, including:\n"
            "- A formal greeting (e.g., 'Dear Hiring Manager,')\n"
            "- An engaging opening paragraph\n"
            "- A body that highlights relevant experience, skills, and motivation for the role\n"
            "- A strong closing paragraph\n"
            "- A professional sign-off (e.g., 'Sincerely, [Your Name]')\n"
            "Do NOT use markdown formatting, bullet points, or section headers. Write as a real letter.\n"
            f"\nResume:\n{resume_text}"
        )
        return handle_llm_fallback("You are a professional cover letter writer.", fallback_prompt, 1000, "cover letter generation")

def clean_generate_interview_questions(resume_text: str):
    """Wrapper for generate_interview_questions with cleaning applied."""
    try:
        result = generate_interview_questions(resume_text)
        return clean_llm_output(result)
    except Exception as e:
        logger.error(f"❌ Interview question generation failed: {str(e)}")
        # Try local fallback for interview questions
        fallback_prompt = f"Generate 5 technical and 5 behavioral interview questions based on this resume:\n\n{resume_text}"
        return handle_llm_fallback("You are an interview coach.", fallback_prompt, 700, "interview questions")

# Tool definitions with cleaned wrapper functions
resume_parser_tool = Tool(name="Resume Extractor", func=clean_extract_resume_data)
resume_match_tool = Tool(name="Resume Matcher", func=clean_match_similar_resumes)
resume_enhancer_tool = Tool(name="Resume Enhancer", func=clean_enhance_resume)
career_path_tool = Tool(name="Career Strategist", func=clean_recommend_career_paths)
course_tool = Tool(name="Intelligent Course Recommender", func=clean_fetch_intelligent_courses)
cover_letter_tool = Tool(name="Cover Letter Generator", func=clean_generate_cover_letter)
interview_tool = Tool(name="Interview Question Generator", func=clean_generate_interview_questions)

# Export the tools for agent usage
all_tools = [
    resume_parser_tool,
    resume_match_tool,
    resume_enhancer_tool,
    career_path_tool,
    course_tool,
    cover_letter_tool,
    interview_tool
]
