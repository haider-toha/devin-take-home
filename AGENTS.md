# AGENTS.md

## Project Overview
This is a GitHub Issue Analysis and Implementation Tool that integrates with Devin AI to automatically analyze GitHub issues and create pull requests with solutions.

## Setup Commands
- Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
- Frontend: `cd frontend && npm install && npm run dev`
- Docker: `docker-compose up --build`

## Architecture
- **Backend**: FastAPI Python application (`backend/`)
  - `main.py` - API endpoints and routing
  - `devin_service.py` - Devin AI integration
  - `github_service.py` - GitHub API integration
  - `config.py` - Configuration management
- **Frontend**: React TypeScript application (`frontend/`)
  - Vite build system
  - Tailwind CSS for styling
  - API integration with backend

## Code Style
- Python: Follow PEP 8, use type hints
- TypeScript: Strict mode enabled
- Use ESLint and Prettier configurations
- Follow conventional commit format

## Testing Guidelines
- Backend: pytest for unit tests
- Frontend: Jest/Vitest for testing
- Run tests before committing
- Maintain test coverage

## Development Workflow
- Create feature branches from `main`
- Use pull requests for code review
- Include issue numbers in commit messages
- Update documentation for new features

## Environment Variables Required
- `GITHUB_TOKEN` - GitHub API access
- `GITHUB_REPO` - Repository in format "owner/repo"
- `DEVIN_API_KEY` - Devin AI API key
- `DEVIN_BASE_URL` - Devin API base URL

## Key Features
1. **Issue Analysis**: Analyze GitHub issues using Devin AI
2. **Unified Workflow**: Combined analysis + implementation
3. **Session Polling**: Real-time status updates with 6000s timeout
4. **Error Handling**: Robust error recovery and fallback mechanisms
5. **GitHub Integration**: Automatic PR creation and issue commenting

## Important Notes
- Sessions poll every 6 seconds with 6000 second timeout
- Supports both analysis-only and unified (analysis + implementation) modes
- Includes fallback mechanisms for API failures
- Maintains session state and provides live progress tracking
