# crew/config.py

from crewai import Crew
from crew.agent import (
    profile_analyst_agent,
    resume_matcher_agent,
    resume_enhancer_agent,
    career_strategy_agent,
    learning_advisor_agent,
    cover_letter_agent,
    interview_prep_agent
)
from crew.tasks import (
    extract_resume_task,
    match_resume_task,
    enhance_resume_task,
    career_path_task,
    recommend_courses_task,
    cover_letter_task,
    interview_question_task
)

# Ordered Crew Setup (based on dependency chain)
career_counselor_crew = Crew(
    agents=[
        profile_analyst_agent,
        resume_matcher_agent,
        resume_enhancer_agent,
        career_strategy_agent,
        learning_advisor_agent,
        cover_letter_agent,
        interview_prep_agent
    ],
    tasks=[
        extract_resume_task,
        match_resume_task,
        enhance_resume_task,
        career_path_task,
        recommend_courses_task,
        cover_letter_task,
        interview_question_task
    ],
    verbose=True,
    process= "sequential"
)

# Optional: Define run function for execution
def run_pipeline(resume_text: str):
    result = career_counselor_crew.run(resume_text)
    return result
