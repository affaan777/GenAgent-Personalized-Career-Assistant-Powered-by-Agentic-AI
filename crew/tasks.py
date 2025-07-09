from crewai import Task
from crew.agent import (
    profile_analyst_agent,
    resume_matcher_agent,
    resume_enhancer_agent,
    career_strategy_agent,
    learning_advisor_agent,
    cover_letter_agent,
    interview_prep_agent
)

# 1. Extract resume
extract_resume_task = Task(
    description="Extract key skills and experience from the uploaded resume. Focus on technical skills, programming languages, frameworks, and work experience. If API fails, provide basic extraction.",
    expected_input="Plain text resume.",
    expected_output="Dictionary with 'skills' and 'experience' keys. Skills should be a list of technical competencies. Experience should be a summary of work history.",
    agent=profile_analyst_agent
)

# 2. Match similar resumes
match_resume_task = Task(
    description="Find top 3 similar resumes from stored index using vector similarity, then use LLM to analyze, score (1-10), and explain the best matches. Output should include clickable links, scores, and reasoning. If LLM or API fails, provide basic similarity results.",
    expected_input="Resume text.",
    expected_output="Markdown list of top 3 resume matches, each with a clickable link, LLM-generated similarity score (1-10), and a brief explanation. If LLM fails, show basic similarity links.",
    agent=resume_matcher_agent
)

# 3. Enhance resume
enhance_resume_task = Task(
    description="Rewrite resume with a professional summary, headline, and missing skills for a target job role. Use clean markdown formatting. If API fails, use local fallback for basic enhancement.",
    expected_input="Resume text and target job role.",
    expected_output="Enhanced ATS-friendly resume text with professional summary, improved formatting, and relevant skills highlighted.",
    agent=resume_enhancer_agent
)

# 4. Recommend career paths
career_path_task = Task(
    description="Recommend 3 job roles based on skills in the resume. Provide role titles, brief descriptions, and why they match the skillset. If API fails, use local fallback for basic recommendations.",
    expected_input="List of skills from resume.",
    expected_output="3 career roles with titles, descriptions, and skill alignment justifications in markdown format.",
    agent=career_strategy_agent
)

# 5. Recommend intelligent courses
recommend_courses_task = Task(
    description="Use AI-powered intelligent course filtering and ranking to recommend the best courses from Coursera and YouTube. Analyze course relevance, skill gaps, learning level, and career impact. Provide personalized recommendations with detailed analysis including relevance scores, skill coverage, and reasoning. If external APIs fail, use local fallback to suggest general learning paths.",
    expected_input="Resume text and target job role.",
    expected_output="Intelligently ranked and filtered course recommendations with relevance scores (1-10), skill gap analysis, learning levels, and detailed reasoning for each recommendation. Include both Coursera and YouTube courses with clickable links.",
    agent=learning_advisor_agent
)

# 6. Generate cover letter
cover_letter_task = Task(
    description="Generate a professional cover letter based on resume and suggested job role. The letter should be in standard business letter format: greeting, opening, body, closing, and sign-off. Do NOT use markdown, bullet points, or section headers. If API fails, use local fallback.",
    expected_input="Resume text and job title.",
    expected_output="A professional cover letter in real letter format, with greeting, body, closing, and signature. No markdown or sections.",
    agent=cover_letter_agent
)

# 7. Generate interview questions
interview_question_task = Task(
    description="Generate 5 technical and 5 behavioral interview questions based on resume and job title. Questions should be relevant to the candidate's background and the target role. If API fails, use local fallback.",
    expected_input="Resume and job role.",
    expected_output="List of 10 interview questions (5 technical, 5 behavioral) formatted clearly with sections.",
    agent=interview_prep_agent
)

# All tasks
all_tasks = [
    extract_resume_task,
    match_resume_task,
    enhance_resume_task,
    career_path_task,
    recommend_courses_task,
    cover_letter_task,
    interview_question_task
]
