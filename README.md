# Devin Issue Assistant

A full-stack web application that integrates GitHub Issues with Devin AI to automatically analyze and implement solutions for repository issues.

## Overview

The Devin Issue Assistant enables you to:
- **List GitHub issues** from any repository
- **Analyze issues with Devin AI** to get confidence scores and implementation plans
- **Execute solutions** automatically using Devin's capabilities
- **Track progress** with an intuitive dashboard

## Architecture

```
┌────────────────────────────────┐
│   React + TypeScript (Vite)    │
│   Modern UI with Tailwind CSS  │
└───────────┬────────────────────┘
            │ REST API
            ▼
┌────────────────────────────────┐
│     FastAPI Backend (Python)   │
│  - GitHub API Integration      │
│  - Devin API Integration       │
│  - In-memory Results Storage   │
└───────────┬────────────────────┘
            │
    ┌───────┴────────┐
    ▼                ▼
┌─────────┐    ┌──────────┐
│ GitHub  │    │  Devin   │
│   API   │    │   API    │
└─────────┘    └──────────┘
```

## Quick Start

### Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 20+** (for frontend)
- **Docker & Docker Compose** (optional, for containerized deployment)
- **GitHub Personal Access Token** with `repo`, `issues`, and `pull_requests` permissions
- **Devin API Key**

### Option 1: Docker Compose (Recommended)

1. **Clone and configure:**
```bash
git clone <repository-url>
cd take-home

# Copy environment template
cp env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

2. **Configure environment variables in `.env`:**
```env
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_REPO=owner/repository-name
DEVIN_API_KEY=your_devin_api_key_here
```

3. **Start the application:**
```bash
# Linux/Mac
chmod +x run-docker.sh
./run-docker.sh

# Or directly with Docker Compose
docker-compose up --build
```

4. **Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Local Development

#### Linux/Mac:
```bash
chmod +x run-local.sh
./run-local.sh
```

#### Windows:
```cmd
run-local.bat
```

#### Manual Setup:

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Configuration

### GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Select repository access and grant these permissions:
   - **Repository permissions:**
     - Issues: Read and write
     - Pull requests: Read and write
     - Contents: Read and write
     - Metadata: Read-only (automatically included)
4. Copy the token to your `.env` file

### Devin API Key

1. Access your Devin account at https://app.devin.ai
2. Navigate to API settings
3. Generate or copy your API key
4. Add it to your `.env` file

### Repository Configuration

Specify the target repository in `owner/repo` format:
```env
GITHUB_REPO=octocat/hello-world
```

## Usage Guide

### 1. View Issues

When you open the application, it automatically fetches and displays all open issues from your configured repository.

**Features:**
- Filter by state (Open, Closed, All)
- View issue details, labels, and metadata
- Direct links to GitHub

### 2. Analyze an Issue

Click the **"Analyze with Devin"** button on any issue card.

**What happens:**
- Devin analyzes the issue content
- Generates a summary of what needs to be done
- Calculates a confidence score (0-100%)
- Creates a step-by-step implementation plan
- Automatically posts the analysis as a comment on the GitHub issue

**Confidence Levels:**
- **70-100%**: High confidence - straightforward implementation
- **40-69%**: Moderate confidence - may require investigation
- **0-39%**: Low confidence - complex or unclear requirements

### 3. Execute the Plan

After analysis, click **"Implement Plan"** to have Devin execute the solution.

**What happens:**
- Devin creates a new session to implement the fix
- Works on the codebase based on the implementation plan
- (Depending on Devin configuration) May create a Pull Request
- Provides a session URL to monitor progress

### 4. Track Progress

- View execution status in real-time
- Access Devin session URLs to see detailed progress
- Check GitHub for new PRs or commits

## API Documentation

### Health Check
```http
GET /health
```
Returns backend configuration status.

### List Issues
```http
GET /api/issues?state=open
```
Query Parameters:
- `state`: `open`, `closed`, or `all` (default: `open`)

### Get Single Issue
```http
GET /api/issues/{issue_number}
```

### Analyze Issue
```http
POST /api/analyze/{issue_number}?post_comment=true
```
Query Parameters:
- `post_comment`: Whether to post analysis as GitHub comment (default: `true`)

Response:
```json
{
  "success": true,
  "issue_number": 123,
  "analysis": {
    "session_id": "session-abc123",
    "summary": "Fix validation bug in login form",
    "confidence": 0.85,
    "steps": [
      "Review login.js validation logic",
      "Update regex pattern",
      "Add unit tests",
      "Update documentation"
    ],
    "status": "completed"
  }
}
```

### Execute Solution
```http
POST /api/execute/{issue_number}
```

Response:
```json
{
  "success": true,
  "issue_number": 123,
  "execution": {
    "session_id": "exec-xyz789",
    "status": "running",
    "message": "Execution started for issue #123",
    "session_url": "https://app.devin.ai/sessions/exec-xyz789"
  }
}
```

### Get Session Status
```http
GET /api/sessions/{session_id}
```

### View History
```http
GET /api/history
```
Returns all analysis and execution history.

## Project Structure

```
take-home/
├── backend/                  # FastAPI backend
│   ├── main.py              # Main FastAPI application
│   ├── config.py            # Configuration management
│   ├── github_service.py    # GitHub API integration
│   ├── devin_service.py     # Devin API integration
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend Docker config
│
├── frontend/                # React + TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Header.tsx
│   │   │   ├── IssueList.tsx
│   │   │   ├── IssueCard.tsx
│   │   │   ├── AnalysisPanel.tsx
│   │   │   └── ConfidenceBar.tsx
│   │   ├── services/
│   │   │   └── api.ts       # API client
│   │   ├── App.tsx          # Main app component
│   │   ├── main.tsx         # Entry point
│   │   └── index.css        # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docker-compose.yml       # Docker Compose config
├── env.example              # Environment template
├── run-local.sh             # Local run script (Linux/Mac)
├── run-local.bat            # Local run script (Windows)
├── run-docker.sh            # Docker run script
└── README.md                # This file
```

## Features

### Frontend
- Modern React 18 with TypeScript
- Tailwind CSS for beautiful, responsive design
- Real-time loading states and error handling
- Animated confidence bars
- Color-coded status indicators
- Direct links to GitHub and Devin sessions

### Backend
- FastAPI with automatic OpenAPI documentation
- Async/await for efficient API calls
- CORS configuration for frontend access
- Comprehensive error handling
- In-memory result caching
- Structured logging

### Integration
- GitHub REST API v3
- Devin API v1
- Automatic comment posting
- Session polling and status tracking
- Fallback analysis when API unavailable

## Security Considerations

- Environment variables for sensitive credentials
- No credentials in source code
- CORS protection
- Token validation on startup
- Use HTTPS in production
- Implement rate limiting for production
- Consider using secrets management (AWS Secrets Manager, etc.)

## Troubleshooting

### Backend won't start
- Verify Python 3.11+ is installed: `python --version`
- Check all environment variables are set in `.env`
- Ensure GitHub token has correct permissions
- Check if port 8000 is available

### Frontend won't start
- Verify Node.js 20+ is installed: `node --version`
- Delete `node_modules` and reinstall: `npm install`
- Check if port 5173 is available

### Issues not loading
- Verify `GITHUB_REPO` format is `owner/repo`
- Check GitHub token has access to the repository
- Review backend logs for API errors

### Devin analysis fails
- Verify `DEVIN_API_KEY` is correct
- Check Devin API quota/limits
- Review backend logs for API errors
- Fallback analysis will be used automatically

### CORS errors
- Ensure backend is running on port 8000
- Check frontend proxy configuration in `vite.config.ts`
- Verify CORS origins in `backend/main.py`

## Production Deployment

### Environment Variables
Add these in your production environment:
```env
GITHUB_TOKEN=<production-token>
GITHUB_REPO=<your-repo>
DEVIN_API_KEY=<production-key>
FRONTEND_URL=https://your-domain.com
BACKEND_PORT=8000
```

### Deployment Options

**Option 1: Docker**
```bash
docker-compose up -d --build
```

**Option 2: Cloud Platforms**
- **Backend**: Deploy to AWS Lambda, Google Cloud Run, or Azure Functions
- **Frontend**: Deploy to Vercel, Netlify, or AWS S3 + CloudFront

**Option 3: Traditional Hosting**
- Build frontend: `cd frontend && npm run build`
- Serve frontend with nginx or similar
- Run backend with gunicorn: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`

## Monitoring

Access FastAPI's built-in documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Backend logs all API calls and errors to console.

## Contributing

This is a take-home project for Cognition Labs. For production use, consider:
- Adding database persistence (PostgreSQL, Redis)
- Implementing user authentication
- Adding webhook support for real-time updates
- Creating comprehensive test suites
- Setting up CI/CD pipelines

## License

This project is created as a take-home assignment for Cognition Labs.

## Next Steps

### For Demo/Presentation:
1. Configure your `.env` file with valid credentials
2. Start the application
3. Create a few test issues in your GitHub repository
4. Walk through the analysis and execution flow
5. Show the Devin session progress

### For Production:
1. Add database persistence
2. Implement authentication
3. Add rate limiting
4. Set up monitoring and alerting
5. Create comprehensive tests
6. Configure CI/CD

## Support

For questions or issues:
- Review API documentation at http://localhost:8000/docs
- Check backend logs for error details
- Verify GitHub and Devin API status
- Review troubleshooting section above

---

**Built for Cognition Labs Take-Home Project**

