from crewai import Agent
from crew.tools import (
    resume_parser_tool,
    resume_match_tool,
    resume_enhancer_tool,
    career_path_tool,
    course_tool,
    cover_letter_tool,
    interview_tool
)

# 1. Profile Analyst: Extracts resume data and triggers embedding
profile_analyst_agent = Agent(
    role="Profile Analyst",
    goal="Extract key insights from the resume including skills and experience. Provide reliable extraction even when external services are limited.",
    backstory="Expert in resume parsing and candidate profiling with fallback capabilities for service interruptions.",
    tools=[resume_parser_tool]
)

# 2. Resume Matcher: Finds similar resumes
resume_matcher_agent = Agent(
    role="Resume Matcher",
    goal="Compare candidate resume with embedded database and return closest matches. Provide helpful feedback when matches are unavailable.",
    backstory="Efficient matching agent using vector similarity for past resumes with graceful handling of service limitations.",
    tools=[resume_match_tool]
)

# 3. Resume Enhancer: Improves formatting, adds summary, fills skill gaps
resume_enhancer_agent = Agent(
    role="Resume Enhancer",
    goal="Improve and modernize the resume with missing skills and summary. Use local fallback when external APIs are unavailable.",
    backstory="Expert resume editor with deep understanding of job requirements and presentation, capable of working with local resources when needed.",
    tools=[resume_enhancer_tool]
)

# 4. Career Strategist: Suggests job roles from skillset
career_strategy_agent = Agent(
    role="Career Strategist",
    goal="Recommend career paths and job roles from extracted skills. Provide valuable insights even with limited external resources.",
    backstory="Helps users align their experience with in-demand career paths using both external APIs and local fallback capabilities.",
    tools=[career_path_tool]
)

# 5. Intelligent Learning Advisor: AI-powered course filtering and ranking
learning_advisor_agent = Agent(
    role="Intelligent Learning Advisor",
    goal="Provide AI-powered intelligent course filtering and ranking from YouTube and Coursera. Analyze course relevance, skill gaps, learning levels, and career impact to deliver personalized recommendations with detailed reasoning and relevance scores.",
    backstory="Advanced learning advisor with sophisticated AI capabilities for course analysis, using LLM-powered relevance scoring, skill gap analysis, and personalized filtering to ensure users get the most beneficial courses for their career goals. Combines multiple data sources with intelligent ranking algorithms.",
    tools=[course_tool]
)

# 6. Cover Letter Generator
cover_letter_agent = Agent(
    role="Cover Letter Writer",
    goal="Generate tailored cover letters based on resume and target role. Ensure quality output even with service limitations.",
    backstory="Expert in professional writing and job market alignment with local fallback capabilities for uninterrupted service.",
    tools=[cover_letter_tool]
)

# 7. Interview Coach
interview_prep_agent = Agent(
    role="Interview Coach",
    goal="Generate mock interview questions based on the resume and job role. Provide relevant questions using available resources.",
    backstory="Helps candidates practice relevant technical and behavioral questions with reliable local fallback when external services are limited.",
    tools=[interview_tool]
)

# Optional export
ALL_AGENTS = [
    profile_analyst_agent,
    resume_matcher_agent,
    resume_enhancer_agent,
    career_strategy_agent,
    learning_advisor_agent,
    cover_letter_agent,
    interview_prep_agent
]
