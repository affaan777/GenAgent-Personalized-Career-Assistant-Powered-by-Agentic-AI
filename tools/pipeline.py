from tools.resume_parser import extract_skills, extract_experience
from tools.llm_api import call_llm_api
from tools.course_fetcher import (
    fetch_intelligent_courses,
    fetch_coursera_courses_from_faiss,
    fetch_youtube_courses
)
from tools.faiss_utils import embed_and_store,FaissHandler
import re
import json
from urllib.parse import quote

# Post-processing function to clean LLM outputs
def clean_llm_output(text: str) -> str:
    """Clean LLM output by removing escape characters and fixing formatting."""
    if not text:
        return text
    
    # Replace literal escape sequences with actual characters
    text = text.replace('\\n', '\n')
    text = text.replace('\\t', '\t')
    text = text.replace('\\r', '\r')
    
    # Replace tab+plus with markdown bullets
    text = text.replace('\t+', '- ')
    text = text.replace('\t-', '- ')
    text = text.replace('\t*', '- ')
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove any remaining literal escape sequences
    text = text.replace('\\n', ' ')
    text = text.replace('\\t', ' ')
    
    # Clean up extra spaces
    text = re.sub(r' +', ' ', text)
    text = text.strip()
    
    return text

# Utility to extract JSON from LLM output (removes markdown code block if present)
def extract_json_from_llm_output(text):
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1)
    # Fallback: find first { ... }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end+1]
    return text.strip()

# 1. Extract structured data from resume

def extract_resume_core_info(resume_text: str):
    """
    Extract skills, job title, professional headline, and summary in a single LLM call.
    Returns a dict with keys: skills, job_title, headline, summary.
    """
    prompt = (
        "You are an expert resume parser and branding coach. Given the following resume, extract:\n"
        "1. Key technical skills (as a Python list of strings, e.g., [\"Python\", \"Machine Learning\"]). If no skills are found, return an empty list.\n"
        "2. The most likely job title (as a short string, e.g., \"Data Scientist\"). If not found, return \"Unknown\".\n"
        "3. A professional headline (max 12 words).\n"
        "4. A 2–3 line professional summary (max 60 words).\n"
        "Respond ONLY in valid JSON as:\n"
        "{\n  \"skills\": [...],\n  \"job_title\": \"...\",\n  \"headline\": \"...\",\n  \"summary\": \"...\"\n}\n"
        "Do not include any text before or after the JSON.\n"
        f"Resume:\n{resume_text}"
    )
    response = call_llm_api(
        role="You are an expert resume parser and branding coach. Extract all requested fields and return only valid JSON.",
        user_prompt=prompt,
        max_tokens=500
    )
    try:
        cleaned_response = extract_json_from_llm_output(response)
        data = json.loads(cleaned_response)
        for key in ["skills", "job_title", "headline", "summary"]:
            if key not in data:
                data[key] = ""
        return data
    except Exception as e:
        print(f"❌ Failed to parse batched LLM response: {e}\nRaw: {response}")
        return {"skills": [], "job_title": "", "headline": "", "summary": ""}

def analyze_resume_matches(query_text: str, matches: list, top_k: int = 3) -> str:
    """
    Return basic FAISS similarity matches as clickable links (no LLM).
    """
    if not matches:
        return "📝 No similar resumes found in the database."
    out = "🔗 **Top Resume Matches:**\n\n"
    for i, match in enumerate(matches, 1):
        meta = match["meta"]
        filename = meta.get("filename", "unknown.pdf")
        clean_name = filename.split("_", 1)[-1]
        # Always use absolute URL with correct extension
        link = f"[📄 {clean_name}](http://192.168.1.10:8000/static/resumes/{filename})"
        out += f"{i}. {link}\n"
    return out.strip()

# 2. Match resume

def match_similar_resumes(query_text: str, filename: str, top_k: int = 3, skills=None, job_title=None) -> str:
    handler = FaissHandler()
    matches = handler.search(query_text, "resume", top_k=top_k+1)  # +1 in case of self-match
    filtered = [m for m in matches if m["meta"].get("filename") != filename]
    filtered = filtered[:top_k]
    if not filtered:
        return analyze_resume_matches(query_text, filtered, top_k)

    backend_url = "http://192.168.1.10:8000"
    matched_resume_texts = "\n".join([
        f"Resume {i+1}: [{m['meta'].get('filename', f'resume_{i+1}.pdf')}]({backend_url}/static/resumes/{quote(m['meta'].get('filename', f'resume_{i+1}.pdf'))})\n{m['text']}"
        for i, m in enumerate(filtered)
    ])
    prompt = (
        f"You are an expert recruiter. Given the following user resume and {top_k} matched resumes, analyze and score each match (1-10) for similarity and relevance.\n"
        "For each match, provide:\n"
        f"- A clickable markdown link to the matched resume (use the provided URL in the format [Resume Name]({backend_url}/static/resumes/filename.pdf))\n"
        "- The similarity score (1-10)\n"
        "- A brief explanation of why it is a good match\n"
        "Format your output as a markdown list. Example:\n"
        f"1. [JohnDoe.pdf]({backend_url}/static/resumes/JohnDoe.pdf) - **Score: 9/10**\n   - Reason: Strong match in data science experience.\n"
        "---\n"
        f"**User Resume:**\n{query_text}\n"
        f"**Matched Resumes:**\n{matched_resume_texts}\n"
        "Respond ONLY in markdown as shown in the example."
    )
    try:
        response = call_llm_api(
            role="You are an expert recruiter and resume matcher. Output only markdown as described.",
            user_prompt=prompt,
            max_tokens=3000
        )
        if response and not response.strip().startswith("❌"):
            return clean_llm_output(response)
        else:
            raise Exception("LLM failed or returned an error.")
    except Exception as e:
        print(f"❌ LLM-powered resume matching failed: {e}")
        if filtered:
            out = "🔗 **Top Resume Matches:**\n\n"
            for i, match in enumerate(filtered, 1):
                meta = match["meta"]
                filename = meta.get("filename", "unknown.pdf")
                filename_encoded = quote(filename)
                clean_name = filename.split("_", 1)[-1]
                link = f"[📄 {clean_name}]({backend_url}/static/resumes/{filename_encoded})"
                out += f"{i}. {link}\n"
            return out.strip()
        else:
            return "📝 No similar resumes found in the database."

# 3. Enhance resume with skills, job role, and LLM summary injection

def enhance_resume(resume_text: str, target_job_role: str = None, skills=None, core_info=None) -> str:
    """
    Generate a full enhanced resume by injecting headline, summary, and skills, rewriting all sections.
    """
    if core_info is None:
        core_info = extract_resume_core_info(resume_text)
    headline = core_info.get("headline", "")
    summary = core_info.get("summary", "")
    skills = core_info.get("skills", skills)
    target_job_role = core_info.get("job_title", target_job_role)

    enhancement_prompt = (
        f"Act as a professional resume editor. Rewrite and enhance the following resume to target the job role of '{target_job_role}'.\n\n"
        f"**Instructions:**\n"
        f"1. **Integrate Headline & Summary:** Start with this professional headline: {headline} and summary: {summary}.\n"
        f"2. **Inject Skills:** Seamlessly incorporate these key skills: {', '.join(skills)}.\n"
        f"3. **Full Rewrite:** Rewrite the entire resume, not just parts of it. Ensure all original sections (Experience, Education, etc.) are present and improved.\n"
        f"4. **Professional Tone:** Use action verbs and quantifiable achievements.\n"
        f"5. **Formatting:** Use clean markdown with clear headers (e.g., `## Experience`) and bullet points (`-`). Do not use any escape characters like \\n.\n\n"
        f"**Original Resume to Enhance:**\n{resume_text}\n\n"
        f"**Return the complete, enhanced resume.**"
    )
    return call_llm_api(
        role="You are a professional resume editor.",
        user_prompt=enhancement_prompt,
        max_tokens=1500
    )


# 4. Recommend career paths based on skills extracted from resume

def recommend_career_paths(skills) -> str:
    if not skills:
        skills = ["general programming", "problem solving"]
    prompt = (
        f"Suggest 3 job roles based on the following skills: {', '.join(skills)}. "
        f"Format your response in clean markdown with clear section headers and bullet points. "
        f"IMPORTANT: Use only markdown formatting (## for headers, - for bullets). "
        f"Do not use any escape characters like \\n, \\t, or \\r. "
        f"Structure your response with job titles as headers and details as bullet points."
    )
    return clean_llm_output(call_llm_api("You are a career strategist.", prompt, max_tokens=300))


# 5. Recommend courses based on job role inferred from resume skills

def fetch_recommended_courses(skills, job_title, resume_text: str) -> str:
    # Use intelligent course fetching with LLM analysis and ranking
    try:
        intelligent_output = fetch_intelligent_courses(resume_text, job_title, max_results=5)
        if not intelligent_output.strip() or "No relevant courses found" in intelligent_output:
            raise ValueError("Intelligent system returned no courses, attempting fallback.")
        return intelligent_output
    except Exception as e:
        print(f"ℹ️ Intelligent course fetching failed or found no results: {e}. Falling back to basic fetch.")
        # Fallback to basic course fetching if intelligent system fails
        try:
            coursera_output = fetch_coursera_courses_from_faiss(job_title, top_k=3)
            youtube_output = fetch_youtube_courses(job_title, max_results=3)
            # Check if fallbacks returned anything
            if ("No Coursera courses found" in coursera_output and "No YouTube videos found" in youtube_output):
                return "📚 No courses found for your profile. Please try again later."
            return (
                f"🎯 **Recommended Job Role**: {job_title}\n\n"
                f"{coursera_output}\n\n"
                f"{youtube_output}"
                f"\n\n*Note: Using basic course recommendations as the intelligent system was unavailable or found no matches.*"
            )
        except Exception as fallback_error:
            # If even the basic fetch fails, return a clear message
            return f"❌ Course recommendation failed: {str(fallback_error)}"


# 6. Generate cover letter based on inferred job title

def generate_cover_letter(skills, job_title, resume_text: str) -> str:
    prompt = (
        f"You are a professional cover letter writer. Write a cover letter for the job title '{job_title}' using the following skills: {', '.join(skills)}. "
        "The letter should:\n"
        "- Be in standard business letter format\n"
        "- Include a formal greeting (e.g., 'Dear Hiring Manager,')\n"
        "- Have an engaging opening paragraph\n"
        "- Highlight relevant experience, skills, and motivation for the role\n"
        "- End with a strong closing paragraph and a professional sign-off (e.g., 'Sincerely, [Your Name]')\n"
        "Do NOT use markdown formatting, bullet points, or section headers. Write as a real letter."
    )
    return call_llm_api(
        role="You are a professional cover letter writer.",
        user_prompt=prompt,
        max_tokens=700
    )


# 7. Generate interview questions for the inferred job role

def generate_interview_questions(skills, job_title, resume_text: str) -> str:
    prompt = (
        f"You are an interview coach. Generate 5 technical and 5 behavioral interview questions for the job title '{job_title}' based on the following skills: {', '.join(skills)}. "
        "Format your response in clean markdown with clear section headers and bullet points. "
        "Use this structure:\n"
        "## Technical Questions\n- Question 1\n- Question 2\n...\n"
        "## Behavioral Questions\n- Question 1\n- Question 2\n..."
    )
    return call_llm_api(
        role="You are an interview coach.",
        user_prompt=prompt,
        max_tokens=500
    )
