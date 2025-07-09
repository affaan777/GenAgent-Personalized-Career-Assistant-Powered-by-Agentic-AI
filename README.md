# GenAgent - Intelligent Career Assistant

GenAgent is a full-stack AI-powered career assistant that helps users analyze, enhance, and match resumes, receive personalized career guidance, and discover relevant learning resources. It combines a FastAPI backend, a Streamlit frontend, and advanced AI/LLM-powered agents for intelligent career support.

## Features

- **Resume Processing:** Upload and analyze resumes with AI-powered insights.
- **Resume Matching:** Find similar resumes from a database using vector similarity and LLM scoring.
- **Resume Enhancement:** Automatically rewrite and enhance resumes for ATS and job fit.
- **Career Guidance:** Get personalized job role recommendations based on your skills and experience.
- **Course Recommendations:** Discover and rank relevant courses from Coursera and YouTube to fill skill gaps.
- **Cover Letter Generation:** Instantly generate tailored cover letters for job applications.
- **Interview Preparation:** Receive mock interview questions (technical and behavioral) based on your resume and target role.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Streamlit (Python)
- **AI/LLM:** Integrates with local and cloud LLMs, vector search (FAISS), and NLP tools

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd GenAgent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Set up environment variables

You can create a `.env` file to configure API keys and other settings. See `shared/config.py` for available options.

## Usage

### Launch with Python (Recommended)

This will start both the backend (FastAPI) and frontend (Streamlit):

```bash
python start_app.py
```

- Backend API: [http://localhost:8000](http://localhost:8000)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Streamlit UI: [http://localhost:8501](http://localhost:8501)

#### Run Backend or Frontend Only

- Backend only: `python start_app.py --backend-only`
- Frontend only: `python start_app.py --frontend-only`

### Launch with Docker

Build and run the app in a container:

```bash
docker build -t genagent .
docker run -p 8000:8000 -p 8501:8501 genagent
```

## Project Structure

```
GenAgent/
  main.py              # FastAPI backend
  start_app.py         # Launcher for backend & frontend
  frontend/app.py      # Streamlit frontend
  crew/                # AI agents, tasks, and tools
  tools/               # NLP, LLM, and pipeline utilities
  shared/              # Shared config
  static/resumes/      # Uploaded resumes
  requirements.txt     # Python dependencies
  Dockerfile           # Docker support
```

## API Endpoints

- `POST /upload` — Upload a PDF resume
- `POST /process_resume` — Upload and process a PDF resume (returns structured info, matches, enhancements, etc.)

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements, bug fixes, or new features.

## License

[MIT](LICENSE) (or specify your license here)

---

**GenAgent** — AI for your career journey 🚀
