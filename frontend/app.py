import streamlit as st
import requests
import json
import pandas as pd
from pathlib import Path
import base64
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="GenAgent - Intelligent Career Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #222; /* Dark background for dark theme */
        color: #f5f5f5;         /* Light text for dark theme */
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'processing_results' not in st.session_state:
    st.session_state.processing_results = {}

def main_page():
    """Main dashboard page."""
    st.markdown('<h1 class="main-header">🧠 GenAgent</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center;">Intelligent Career Assistant</h2>', unsafe_allow_html=True)
    
    # Feature overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 Resume Processing</h3>
            <p>Upload and analyze resumes with AI-powered insights</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Career Guidance</h3>
            <p>Get personalized career recommendations and job matches</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📚 Learning Paths</h3>
            <p>Discover relevant courses and skill development resources</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick stats
    st.subheader("📊 System Status")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Resumes Processed", len(st.session_state.uploaded_files))
    
    with col2:
        st.metric("API Status", "🟢 Online")
    
    with col3:
        st.metric("Database Size", "142+ Resumes")
    
    with col4:
        st.metric("Processing Time", "< 30s")

def upload_page():
    """Resume upload and processing page."""
    st.header("📄 Resume Upload & Processing")
    
    # Upload options
    upload_option = st.radio(
        "Choose upload method:",
        ["Single Resume", "Text Input"]
    )
    
    if upload_option == "Single Resume":
        uploaded_file = st.file_uploader(
            "Upload a PDF resume",
            type=['pdf'],
            help="Upload a single PDF resume for processing"
        )
        
        if uploaded_file and st.button("🚀 Process Resume"):
            with st.spinner("Processing resume..."):
                try:
                    # Prepare file for upload
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')}
                    
                    # Call FastAPI endpoint
                    response = requests.post("http://localhost:8000/process_resume", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.processing_results[uploaded_file.name] = result
                        st.session_state.uploaded_files.append(uploaded_file.name)
                        
                        st.success("✅ Resume processed successfully!")
                        display_results(result)
                    else:
                        st.error(f"❌ Error: {response.text}")
                        
                except Exception as e:
                    st.error(f"❌ Processing failed: {str(e)}")
    
    else:  # Text Input
        resume_text = st.text_area(
            "Paste resume text here:",
            height=300,
            help="Paste the text content of a resume"
        )
        
        if resume_text and st.button("📝 Process Text"):
            with st.spinner("Processing text..."):
                try:
                    # Create a mock file for text processing
                    response = requests.post("http://localhost:8000/process_text", json={
                        "resume_text": resume_text
                    })
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Text processed successfully!")
                        display_results(result)
                    else:
                        st.error(f"❌ Error: {response.text}")
                        
                except Exception as e:
                    st.error(f"❌ Processing failed: {str(e)}")

def display_results(result):
    """Display processing results in a formatted way."""
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 File Information")
        st.write(f"**Filename:** {result.get('filename', 'N/A')}")
        st.write(f"**Processing Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        st.subheader("🔍 Quick Stats")
        if 'structured_resume' in result:
            skills = result['structured_resume'].get('skills', [])
            st.write(f"**Skills Found:** {len(skills)}")
            st.write(f"**Experience:** {'Yes' if result['structured_resume'].get('experience') else 'No'}")
    
    # Structured resume
    if 'structured_resume' in result:
        st.subheader("🎯 Skills & Experience")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Skills:**")
            skills = result['structured_resume'].get('skills', [])
            for skill in skills:
                st.write(f"• {skill}")
        
        with col2:
            st.write("**Experience:**")
            experience = result['structured_resume'].get('experience', 'No experience found')
            st.text_area("Experience Summary", experience, height=100, disabled=True)
    
    # Similar resumes
    if 'matched_resumes' in result:
        st.subheader("🔗 Similar Resumes")
        matches = result['matched_resumes']
        if matches and not matches.startswith("📝 No similar"):
            st.markdown(matches)
        else:
            st.info("No similar resumes found in the database.")
    
    # Enhanced resume
    if 'enhanced_resume' in result:
        st.subheader("✨ Enhanced Resume")
        with st.expander("View Enhanced Resume"):
            st.markdown(result['enhanced_resume'])
    
    # Career paths
    if 'career_paths' in result:
        st.subheader("🎯 Career Recommendations")
        with st.expander("View Career Paths"):
            st.markdown(result['career_paths'])
    
    # Courses
    if 'courses' in result:
        st.subheader("📚 Learning Recommendations")
        with st.expander("View Course Recommendations"):
            st.markdown(result['courses'])
    
    # Cover letter
    if 'cover_letter' in result:
        st.subheader("📝 Cover Letter")
        with st.expander("View Generated Cover Letter"):
            st.markdown(result['cover_letter'])
    
    # Interview questions
    if 'interview_questions' in result:
        st.subheader("❓ Interview Questions")
        with st.expander("View Interview Questions"):
            st.markdown(result['interview_questions'])

# Sidebar navigation
st.sidebar.title("🧠 GenAgent")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigation",
    ["🏠 Dashboard", "📄 Upload & Process", "📊 Results"]
)

# Page routing
if page == "🏠 Dashboard":
    main_page()
elif page == "📄 Upload & Process":
    upload_page()
elif page == "📊 Results":
    st.header("📊 Processing Results")
    
    if not st.session_state.processing_results:
        st.info("No results to display. Process a resume first!")
    else:
        # Select result to display
        selected_file = st.selectbox(
            "Select a processed resume:",
            list(st.session_state.processing_results.keys())
        )
        
        if selected_file:
            result = st.session_state.processing_results[selected_file]
            display_results(result)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Version:** 1.0.0")
st.sidebar.markdown("**Status:** 🟢 Online") 