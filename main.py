# main.py

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from tools.pipeline import (
    extract_resume_core_info,
    match_similar_resumes,
    enhance_resume,
    recommend_career_paths,
    fetch_recommended_courses,
    generate_cover_letter,
    generate_interview_questions
)
from tools.resume_parser import extract_text_from_pdf
import os
from uuid import uuid4
from tools.llm_api import call_llm_api

app = FastAPI(title="GenAgent - Intelligent Career Assistant")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure directory exists
os.makedirs("static/resumes", exist_ok=True)

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    unique_id = str(uuid4())
    saved_path = f"static/resumes/{unique_id}_{file.filename}"
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    # Extract just the filename for consistency
    filename_only = os.path.basename(saved_path)
    return {"filename": filename_only, "message": "✅ Resume uploaded successfully."}

@app.post("/process_resume")
async def process_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    unique_id = str(uuid4())
    saved_path = f"static/resumes/{unique_id}_{file.filename}"
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    try:
        resume_text = extract_text_from_pdf(saved_path)
        filename_only = os.path.basename(saved_path)

        # Validate extracted text
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

        # Batched LLM extraction for all core info
        core_info = extract_resume_core_info(resume_text)
        skills = core_info["skills"]
        job_title = core_info["job_title"]
        # Optionally, you can also use core_info["headline"] and core_info["summary"]

        # Run the optimized pipeline using precomputed core_info
        matches = match_similar_resumes(resume_text, filename_only, skills=skills, job_title=job_title)
        enhanced = enhance_resume(resume_text, target_job_role=job_title, skills=skills, core_info=core_info)
        careers = recommend_career_paths(skills)
        courses = fetch_recommended_courses(skills, job_title, resume_text)
        cover_letter = generate_cover_letter(skills, job_title, resume_text)
        interview = generate_interview_questions(skills, job_title, resume_text)

        return {
            "structured_resume": core_info,
            "matched_resumes": matches,
            "enhanced_resume": enhanced,
            "career_paths": careers,
            "courses": courses,
            "cover_letter": cover_letter,
            "interview_questions": interview,
            "filename": filename_only
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
