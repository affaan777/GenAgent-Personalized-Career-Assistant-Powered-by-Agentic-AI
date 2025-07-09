import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from tools.llm_api import call_llm_api, call_llm_api_json

load_dotenv()

# Load API keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ---------------------- YOUTUBE ------------------------

def fetch_youtube_courses(query: str, max_results: int = 5) -> str:
    """Fetches top YouTube videos for the given course query with clickable links."""
    try:
        if not YOUTUBE_API_KEY:
            return "❌ YouTube API key not configured."
        
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        
        response = youtube.search().list(
            q=f"{query} course tutorial",
            part="snippet",
            type="video",
            maxResults=max_results,
            order="relevance"
        ).execute()
        
        if not response.get("items"):
            return "📺 No YouTube videos found."
        
        result = "📺 **YouTube Courses:**\n\n"
        for i, item in enumerate(response["items"], 1):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Create clickable markdown link
            result += f"{i}. [{title}]({url})\n"
            result += f"   📺 {channel}\n\n"
        
        return result.strip()
        
    except Exception as e:
        print(f"❌ YouTube API error: {e}")
        return "❌ YouTube API failed."

# ---------------------- COURSERA (FAISS-BASED) ------------------------

def fetch_coursera_courses_from_faiss(query: str, top_k: int = 5) -> str:
    """Fetch Coursera courses using FAISS retrieval instead of API calls."""
    try:
        from tools.faiss_utils import FaissHandler
        
        handler = FaissHandler()
        
        # Check if Coursera data exists in FAISS
        coursera_corpus = handler.get_corpus("coursera")
        
        if not coursera_corpus:
            # If no Coursera data exists, return a message
            return "📚 No Coursera courses found in database. Please add courses first."
        
        # Search for relevant courses
        results = handler.search(query, "coursera", top_k)
        
        if not results:
            return "📚 No relevant Coursera courses found."
        
        # Format results with clickable links
        result = "📚 **Coursera Courses:**\n\n"
        for i, course_result in enumerate(results, 1):
            meta = course_result["meta"]
            title = meta.get("title", "Unknown Course")
            url = meta.get("url", "#")
            institution = meta.get("institution", "Unknown Institution")
            rating = meta.get("rating", "")
            similarity = course_result["similarity"] * 100
            
            # Create clickable markdown link
            result += f"{i}. [{title}]({url})\n"
            result += f"   🎓 {institution}"
            if rating:
                result += f" - ⭐ {rating}"
            result += f" - **{similarity:.1f}% Match**\n\n"
        
        return result.strip()
        
    except Exception as e:
        print(f"❌ Coursera FAISS error: {e}")
        return f"❌ Coursera retrieval failed: {str(e)}"

def add_coursera_course_to_faiss(title: str, url: str, institution: str, rating: str = "", description: str = ""):
    """Add a Coursera course to the FAISS database for future retrieval."""
    try:
        from tools.faiss_utils import FaissHandler
        
        handler = FaissHandler()
        
        # Create course text for embedding
        course_text = f"{title} {institution} {description}".strip()
        
        # Create metadata
        meta = {
            "title": title,
            "url": url,
            "institution": institution,
            "rating": rating,
            "type": "coursera"
        }
        
        # Add to FAISS
        result = handler.add(course_text, meta, "coursera")
        return result
        
    except Exception as e:
        print(f"❌ Error adding course to FAISS: {e}")
        return f"❌ Failed to add course: {str(e)}"

# ---------------------- INTELLIGENT COURSE FILTERING & RANKING ------------------------

def analyze_course_relevance(course_data: dict, user_skills: list, target_role: str) -> dict:
    """
    Analyze course relevance using LLM for intelligent filtering.
    
    Args:
        course_data: Dictionary containing course information
        user_skills: List of user's current skills
        target_role: Target job role
    
    Returns:
        Dictionary with relevance score and analysis
    """
    try:
        # Defensive: skip or fix if course_data is not a dict
        if not isinstance(course_data, dict):
            print(f"⚠️ Skipping course_data because it is not a dict: {course_data}")
            return {
                "relevance_score": 0,
                "skill_gaps_covered": [],
                "learning_level": "Unknown",
                "career_impact": "Unknown",
                "recommendation": "Not Recommended",
                "reasoning": "Invalid course data format"
            }
        
        # Prepare course information
        course_title = course_data.get("title", "")
        course_description = course_data.get("description", "")
        course_institution = course_data.get("institution", "")
        course_rating = course_data.get("rating", "")
        
        # Create analysis prompt
        analysis_prompt = f"""
        Analyze the relevance of this course for a user with the following profile:
        
        **User Skills:** {', '.join(user_skills)}
        **Target Role:** {target_role}
        
        **Course Information:**
        - Title: {course_title}
        - Institution: {course_institution}
        - Rating: {course_rating}
        - Description: {course_description}
        
        Please provide:
        1. Relevance Score (1-10): How well does this course align with the user's skills and target role?
        2. Skill Gap Coverage: Which missing skills does this course address?
        3. Learning Level: Is this course suitable for the user's current level (Beginner/Intermediate/Advanced)?
        4. Career Impact: How will this course help in achieving the target role?
        5. Recommendation: Strongly Recommend/Recommend/Consider/Not Recommended
        
        Format your response as JSON:
        {{
            "relevance_score": 8,
            "skill_gaps_covered": ["skill1", "skill2"],
            "learning_level": "Intermediate",
            "career_impact": "High impact for target role",
            "recommendation": "Strongly Recommend",
            "reasoning": "Brief explanation"
        }}
        """
        
        # Call LLM for analysis with JSON expectation
        analysis = call_llm_api_json(
            role="You are an expert learning advisor and career coach. Analyze course relevance objectively and return only valid JSON.",
            user_prompt=analysis_prompt,
            max_tokens=500
        )
        
        # First, check for API or parsing errors.
        if isinstance(analysis, dict) and "error" in analysis:
            print(f"⚠️ LLM analysis failed: {analysis.get('raw_response', analysis['error'])}")
            return {
                "relevance_score": 1, "skill_gaps_covered": [], "learning_level": "Unknown",
                "career_impact": "Moderate", "recommendation": "Consider",
                "reasoning": "Analysis failed or was unavailable."
            }

        # Handle case where LLM returns a list with a single dict
        if isinstance(analysis, list) and analysis:
            analysis = analysis[0]

        # After potentially unpacking the list, ensure we have a dictionary
        if not isinstance(analysis, dict):
            print(f"❌ Analysis did not produce a valid dictionary. Received: {analysis}")
            return {
                "relevance_score": 1,
                "skill_gaps_covered": [],
                "learning_level": "Unknown",
                "career_impact": "Moderate",
                "recommendation": "Consider",
                "reasoning": "Analysis returned an invalid format."
            }
        
        return analysis
                
    except Exception as e:
        print(f"❌ Course analysis failed: {e}")
        return {
            "relevance_score": 1,
            "skill_gaps_covered": [],
            "learning_level": "Unknown",
            "career_impact": "Moderate",
            "recommendation": "Consider",
            "reasoning": f"Analysis error: {str(e)}"
        }

def rank_and_filter_courses(courses: list, user_skills: list, target_role: str, max_results: int = 5) -> list:
    """
    Rank and filter courses based on LLM analysis.
    
    Args:
        courses: List of course dictionaries
        user_skills: List of user's current skills
        target_role: Target job role
        max_results: Maximum number of courses to return
    
    Returns:
        List of ranked and filtered courses
    """
    try:
        # Analyze each course
        analyzed_courses = []
        for course in courses:
            if not isinstance(course, dict):
                print(f"⚠️ Skipping non-dict course: {course}")
                continue
            analysis = analyze_course_relevance(course, user_skills, target_role)
            course_with_analysis = {
                **course,
                "analysis": analysis,
                "relevance_score": analysis.get("relevance_score", 5)
            }
            analyzed_courses.append(course_with_analysis)
        
        # Sort by relevance score (highest first)
        ranked_courses = sorted(analyzed_courses, key=lambda x: x["relevance_score"], reverse=True)
        
        # Filter out low-relevance courses (score < 5)
        filtered_courses = [course for course in ranked_courses if course["relevance_score"] >= 5]
        
        # Return top results
        return filtered_courses[:max_results]
        
    except Exception as e:
        print(f"❌ Course ranking failed: {e}")
        return []  # Return empty list if ranking fails

def format_intelligent_course_recommendations(courses: list, user_skills: list, target_role: str) -> str:
    """
    Format course recommendations with intelligent analysis and ranking.
    
    Args:
        courses: List of ranked course dictionaries
        user_skills: List of user's current skills
        target_role: Target job role
    
    Returns:
        Formatted markdown string with course recommendations
    """
    if not courses:
        return "📚 No relevant courses found for your profile."
    
    result = f"🎯 **Intelligent Course Recommendations for {target_role}**\n\n"
    result += f"**Your Skills:** {', '.join(user_skills)}\n\n"
    
    for i, course in enumerate(courses, 1):
        analysis = course.get("analysis", {})
        title = course.get("title", "Unknown Course")
        url = course.get("url", "#")
        institution = course.get("institution", "Unknown Institution")
        rating = course.get("rating", "")
        relevance_score = analysis.get("relevance_score", 5)
        recommendation = analysis.get("recommendation", "Consider")
        learning_level = analysis.get("learning_level", "Unknown")
        skill_gaps = analysis.get("skill_gaps_covered", [])
        reasoning = analysis.get("reasoning", "")
        
        # Create clickable link
        result += f"**{i}. [{title}]({url})**\n"
        result += f"   🎓 {institution}"
        if rating:
            result += f" - ⭐ {rating}"
        result += f" - 📊 **{relevance_score}/10 Relevance**\n"
        result += f"   🎯 **{recommendation}** - Level: {learning_level}\n"
        
        if skill_gaps:
            result += f"   🔧 **Skills Covered:** {', '.join(skill_gaps)}\n"
        
        if reasoning:
            result += f"   💡 **Why:** {reasoning}\n"
        
        result += "\n"
    
    return result.strip()

def fetch_intelligent_courses(resume_text: str, target_role: str = None, max_results: int = 5) -> str:
    """
    Fetch and intelligently rank courses using LLM analysis.
    
    Args:
        resume_text: User's resume text
        target_role: Target job role (optional)
        max_results: Maximum number of courses to return
    
    Returns:
        Formatted course recommendations with intelligent analysis
    """
    try:
        from tools.resume_parser import extract_skills
        
        # Extract user skills from resume
        user_skills = extract_skills(resume_text)
        if not user_skills:
            user_skills = ["general programming", "problem solving"]
        
        # Determine target role if not provided
        if not target_role:
            role_prompt = f"Based on these skills: {', '.join(user_skills)}, suggest the most suitable job role. Return only the job title."
            target_role = call_llm_api(
                role="You are a career advisor. Suggest the most suitable job role.",
                user_prompt=role_prompt,
                max_tokens=50
            ).strip()
        
        # Fetch courses from both sources
        all_courses = []
        
        # Get Coursera courses
        try:
            from tools.faiss_utils import FaissHandler
            handler = FaissHandler()
            coursera_results = handler.search(target_role, "coursera", max_results * 2)
            
            for result in coursera_results:
                meta = result["meta"]
                course_data = {
                    "title": meta.get("title", ""),
                    "url": meta.get("url", ""),
                    "institution": meta.get("institution", ""),
                    "rating": meta.get("rating", ""),
                    "description": f"Coursera course: {meta.get('title', '')}",
                    "source": "Coursera",
                    "similarity": result["similarity"]
                }
                all_courses.append(course_data)
        except Exception as e:
            print(f"⚠️ Coursera fetch failed: {e}")
        
        # Get YouTube courses (simplified for now)
        try:
            if YOUTUBE_API_KEY:
                youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
                response = youtube.search().list(
                    q=f"{target_role} course tutorial",
                    part="snippet",
                    type="video",
                    maxResults=max_results,
                    order="relevance"
                ).execute()
                
                for item in response.get("items", []):
                    course_data = {
                        "title": item["snippet"]["title"],
                        "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                        "institution": item["snippet"]["channelTitle"],
                        "rating": "",
                        "description": item["snippet"]["description"],
                        "source": "YouTube",
                        "similarity": 0.8  # Default similarity for YouTube
                    }
                    all_courses.append(course_data)
        except Exception as e:
            print(f"⚠️ YouTube fetch failed: {e}")
        
        if not all_courses:
            return "📚 No courses found. Please try a different search term."
        
        # Rank and filter courses
        ranked_courses = rank_and_filter_courses(all_courses, user_skills, target_role, max_results)
        
        # Format recommendations
        return format_intelligent_course_recommendations(ranked_courses, user_skills, target_role)
        
    except Exception as e:
        print(f"❌ Intelligent course fetching failed: {e}")
        return f"❌ Course recommendation failed: {str(e)}"
