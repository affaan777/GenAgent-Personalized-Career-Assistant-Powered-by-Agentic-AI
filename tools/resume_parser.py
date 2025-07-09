import pdfplumber
import spacy
from tools.llm_api import call_llm_api

# ✅ Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# 📄 Extract full text from a resume PDF
def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

# 🧠 Extract keyword-based technical skills
def extract_skills(text: str) -> list[str]:
    """
    Extracts key skills from resume text using an LLM for better accuracy.
    Falls back to spaCy on a 'Skills' section, and finally to a keyword list.
    """
    prompt = f"""
    Based on the following resume text, extract the key technical skills, tools, and technologies.

    **Instructions:**
    - List only the skills, separated by commas.
    - Do not add any introductory text, explanations, or labels like "Skills:".
    
    **Resume Text:**
    ---
    {text}
    ---
    """
    
    try:
        role = "You are an expert resume parser. Your task is to identify technical skills and respond with ONLY a single line of comma-separated values."
        response = call_llm_api(role, prompt, max_tokens=250)
        
        skills = [skill.strip() for skill in response.split(',') if skill.strip()]
        
        if skills:
            return list(set(skills))
        else:
            raise ValueError("LLM returned no skills.")

    except Exception as e:
        print(f"⚠️ LLM-based skill extraction failed: {e}. Falling back to spaCy and keyword search.")
        
        # Fallback 1: Use spaCy to parse a dedicated 'Skills' section
        try:
            lines = text.split('\\n')
            in_skills_section = False
            skills_text = ""
            for line in lines:
                # Identify the start of the skills section
                if any(keyword in line.lower() for keyword in ['skills', 'technologies', 'tools']):
                    in_skills_section = True
                    skills_text += line.split(":", 1)[-1] if ":" in line else " " + line.strip()
                    continue

                # Identify the end of the skills section
                if in_skills_section and any(keyword in line.lower() for keyword in ['experience', 'employment', 'work history', 'education', 'projects']):
                    in_skills_section = False
                    continue
                
                if in_skills_section:
                    skills_text += " " + line.strip()

            if skills_text.strip():
                doc = nlp(skills_text)
                # Extract noun phrases and proper nouns, which are likely skills
                spacy_skills = [chunk.text.strip() for chunk in doc.noun_chunks]
                spacy_skills.extend([token.text.strip() for token in doc if token.pos_ == "PROPN"])
                
                if spacy_skills:
                    # Filter out single-character tokens and convert to lowercase
                    cleaned_skills = [skill.lower() for skill in spacy_skills if len(skill) > 1]
                    print(f"✅ Extracted skills from 'Skills' section using spaCy.")
                    return list(set(cleaned_skills))
        except Exception as spacy_error:
            print(f"⚠️ spaCy 'Skills' section parsing failed: {spacy_error}. Proceeding to final fallback.")

        # Fallback 2: A more comprehensive keyword search as a last resort
        print("Falling back to basic keyword search.")
        skill_keywords = [
            "python", "java", "c++", "c#", "javascript", "typescript", "html", "css", "sql", "nosql",
            "machine learning", "deep learning", "data science", "natural language processing", "nlp",
            "computer vision", "cv", "data analysis", "data visualization", "statistics",
            "cloud computing", "aws", "azure", "google cloud", "gcp",
            "docker", "kubernetes", "git", "linux", "bash", "shell",
            "react", "angular", "vue.js", "node.js", "express.js",
            "django", "flask", "fastapi", "spring", "langchain", "langgraph",
            "pandas", "numpy", "scikit-learn", "matplotlib", "seaborn",
            "tensorflow", "pytorch", "keras",
            "agile", "scrum", "jira"
        ]
        text_lower = text.lower()
        found_skills = [skill for skill in skill_keywords if skill in text_lower]
        return list(set(found_skills))

def extract_experience(text: str) -> list[str]:
    """
    Extracts professional experience from resume text.
    (This is a placeholder and can be improved with more sophisticated parsing)
    """
    experience_section = []
    in_experience_section = False
    for line in text.split('\n'):
        if any(keyword in line.lower() for keyword in ['experience', 'employment', 'work history']):
            in_experience_section = True
            continue
        if any(keyword in line.lower() for keyword in ['education', 'skills', 'projects']):
            in_experience_section = False
            continue
        if in_experience_section and line.strip():
            experience_section.append(line.strip())
    return experience_section

