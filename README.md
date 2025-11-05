# Devin Issue Assistant

A full-stack web app integrating GitHub Issues with Devin AI to automatically analyze and implement solutions for repository issues.

---

## Overview

The Devin Issue Assistant helps engineering teams:

- **List GitHub issues** with filtering and sorting  
- **Analyze issues** using Devin AI with confidence scores and implementation plans  
- **Execute solutions** automatically  
- **Track progress** with loading screens and session monitoring  
- **Maintain context** with automatic GitHub comments and caching  

---

## Architecture

### System Architecture

The application follows a three-tier architecture:

**Frontend Layer**: React + TypeScript application built with Vite and styled with Tailwind CSS
**Backend Layer**: FastAPI + Python 3.11 server with configuration management, GitHub service integration, Devin service integration, and in-memory caching
**External Services**: GitHub REST API v3 for issue management and Devin API v1 for AI-powered analysis and implementation

### Frontend Component Hierarchy

- `main.tsx` (Entry Point)
  - `App.tsx` (Root Component)
    - `Header.tsx` (Repository Information)
    - `IssueList.tsx` (Issue Manager)
      - `IssueCard.tsx` (Individual Issue Display)
        - `AnalysisPanel.tsx` (Analysis Results)
        - `SimpleLoadingScreen.tsx` (Static Loading Screen)
      - `ConfidenceBar.tsx` (Visual Score Display)

### Backend Service Layer

- `main.py` (FastAPI Application)
  - `config.py` (Environment Configuration Management)
  - `github_service.py` (GitHub Integration Service)
    - Issue Fetching
    - Comment Posting
  - `devin_service.py` (Devin AI Integration Service)
    - Session Creation
    - Status Polling
    - Response Parsing
    - Stream Processing
  - In-Memory Store (`issue_results` dictionary for caching)

---

## Data Flow

### Complete Analysis Flow

1. Engineer clicks "Analyze & Implement" on an issue in the frontend
2. Frontend sends POST request to `/api/analyze/123` (where 123 is the issue number)
3. Backend fetches issue #123 details from GitHub API
4. Backend receives issue data from GitHub
5. Backend sends analysis and implementation request to Devin AI with instructions: analyze → implement → create PR
6. Devin AI confirms task has started
7. Backend polls Devin every 10 seconds (maximum 900 seconds timeout):
   - While running: Devin analyzes requirements, modifies code, and pushes changes to create PR #45
8. Devin returns completion status with PR #45 information
9. Backend posts comment on original issue: "PR created: #45"
10. Backend returns analysis + PR info to frontend
11. Frontend displays PR link and summary to engineer

### Loading Screen Flow

1. Frontend sends POST `/api/analyze/{issue_number}` to backend
2. Backend creates analysis session with Devin
3. Backend returns Session ID to frontend for polling
4. Frontend displays SimpleLoadingScreen
5. While session is running:
   - Frontend polls GET `/api/sessions/{session_id}`
   - Backend checks session status with Devin via GET `/sessions/{session_id}`
   - Devin returns status, messages, and analysis data
   - Backend forwards session status to frontend
   - If session completed: Frontend hides loading screen and shows analysis
   - If session still running: Frontend continues showing loading screen

---

## Setup & Deployment

### Prerequisites

- Python 3.11+ (Backend)
- Node.js 20+ (Frontend)
- Docker & Docker Compose (Optional)
- GitHub Personal Access Token with `repo`, `issues`, `pull_requests` permissions
- Devin API Key

### Running with Docker Compose

1. Clone the repository and configure environment variables in `.env` file
2. Run `docker-compose up --build`
3. Access the application:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000

### Local Development

1. Start backend with Python and FastAPI
2. Start frontend with `npm run dev` in the frontend directory

---

## Usage

- **View Issues**: Lists all open issues with filtering and sorting capabilities
- **Analyze Issue**: Generates structured analysis including summary, confidence score, implementation steps, complexity assessment, potential challenges, and success criteria
- **Execute Plan**: Devin autonomously creates a pull request with the implemented solution
- **Analyze & Implement**: Single button that performs both analysis and implementation in one workflow
- **Track Progress**: Loading screen shows real-time session status and progress updates

---

## Future Enhancements

### High Priority
- Database persistence for analysis results
- Multi-user authentication and authorization
- Webhook integration for real-time updates
- Comprehensive test suite

### Medium Priority
- Batch processing for multiple issues
- Issue prioritization algorithms
- Email and notification system
- Analytics dashboard

### Low Priority
- Custom prompt templates
- Issue template integration
- Multi-repository support
- AI model selection options

---

## Security & Monitoring

- All credentials stored in environment variables
- Token validation performed on application startup
- CORS restricted to frontend URLs only
- Input validation on all API endpoints
- HTTPS strongly recommended for production deployments
- Rate limiting and secrets management advised for production use

Backend includes comprehensive logging for API calls and errors. FastAPI automatic documentation available at `/docs` endpoint for API monitoring and testing.
