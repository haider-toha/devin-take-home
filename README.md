# Devin Issue Assistant

A full-stack web application that integrates GitHub Issues with Devin AI to automatically analyze and implement solutions for repository issues.

## Overview

The Devin Issue Assistant enables engineering teams to:
- **List GitHub issues** from any repository with filtering and sorting
- **Analyze issues with Devin AI** to generate confidence scores and detailed implementation plans
- **Execute solutions** automatically using Devin's autonomous capabilities
- **Track progress** with clean loading screens and session monitoring
- **Maintain context** with automatic GitHub comment posting and in-memory result caching

## Architecture

### System Architecture

The application follows a modern three-tier architecture with API-based integration to external services:

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React + TypeScript<br/>Vite + Tailwind CSS]
    end

    subgraph "Backend Layer"
        B[FastAPI + Python 3.11]
        C[Configuration Manager]
        D[GitHub Service]
        E[Devin Service]
        F[In-Memory Cache]
    end

    subgraph "External Services"
        G[GitHub REST API v3]
        H[Devin API v1]
    end

    A -->|REST API| B
    B --> C
    B --> D
    B --> E
    B --> F
    D -->|Authentication<br/>Issue Management<br/>Comment Posting| G
    E -->|Session Creation<br/>Status Polling<br/>Response Parsing| H

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style G fill:#f0f0f0
    style H fill:#f0f0f0
```

### Component Architecture

#### Frontend Component Hierarchy

```mermaid
graph TD
    A[main.tsx<br/>Entry Point] --> B[App.tsx<br/>Root Component]
    B --> C[Header.tsx<br/>Repository Info]
    B --> D[IssueList.tsx<br/>Issue Manager]
    D --> E[IssueCard.tsx<br/>Individual Issue]
    E --> F[AnalysisPanel.tsx<br/>Analysis Results]
    E --> G[SimpleLoadingScreen.tsx<br/>Static Loading Screen]
    F --> H[ConfidenceBar.tsx<br/>Visual Score Display]

    style B fill:#4a90e2
    style D fill:#50c878
    style E fill:#f5a623
    style F fill:#bd10e0
```

#### Backend Service Layer

```mermaid
graph LR
    A[main.py<br/>FastAPI App] --> B[config.py<br/>Environment Config]
    A --> C[github_service.py<br/>GitHub Integration]
    A --> D[devin_service.py<br/>Devin Integration]
    A --> E[In-Memory Store<br/>issue_results dict]

    C --> F[Issue Fetching]
    C --> G[Comment Posting]

    D --> H[Session Creation]
    D --> I[Status Polling]
    D --> J[Response Parsing]
    D --> K[Stream Processing]

    style A fill:#ff6b6b
    style C fill:#4ecdc4
    style D fill:#95e1d3
```

### Data Flow

#### Complete Analysis Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant GitHub
    participant Devin

    User->>Frontend: Click "Analyze with Devin"
    Frontend->>Backend: POST /api/analyze/{issue_number}

    Backend->>GitHub: GET /repos/{owner}/{repo}/issues/{number}
    GitHub-->>Backend: Issue data (title, body, labels)

    Backend->>Devin: POST /v1/sessions<br/>(Create analysis session)
    Devin-->>Backend: session_id

    loop Poll every 5s (max 300s)
        Backend->>Devin: GET /sessions/{session_id}?include_messages=true
        Devin-->>Backend: status, messages, thinking_steps
        alt Status is completed
            Backend->>Backend: Parse response (JSON/Text)
            Backend->>Backend: Extract summary, confidence, steps
        end
    end

    alt post_comment=true
        Backend->>GitHub: POST /issues/{number}/comments<br/>(Post analysis as comment)
        GitHub-->>Backend: comment_id
    end

    Backend-->>Frontend: Analysis result
    Frontend-->>User: Display AnalysisPanel
```

#### Unified Analysis + Implementation Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Devin
    participant GitHub

    User->>Frontend: Click "Analyze & Implement"
    Frontend->>Backend: POST /api/analyze/{issue_number}?unified=true

    Backend->>Devin: POST /v1/sessions<br/>(Unified session: analyze + implement)
    Devin-->>Backend: session_id

    loop Poll every 10s (max 900s)
        Backend->>Devin: GET /sessions/{session_id}
        Devin-->>Backend: status, output

        alt Status is running
            Devin->>GitHub: (Autonomous) Clone repo, make changes
            Devin->>GitHub: (Autonomous) Create PR
        end
    end

    Backend->>Backend: Extract PR URL from response
    Backend->>GitHub: POST /issues/{number}/comments<br/>(Post analysis + PR link)

    Backend-->>Frontend: Analysis + execution result
    Frontend-->>User: Display PR link
```

#### Loading Screen Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant Backend
    participant Devin

    Frontend->>Backend: POST /api/analyze/{issue_number}
    Backend->>Devin: Create analysis session
    Backend-->>Frontend: Session ID (for polling)
    Frontend->>Frontend: Show SimpleLoadingScreen

    loop While session is running
        Frontend->>Backend: GET /api/sessions/{session_id}
        Backend->>Devin: GET /sessions/{session_id}
        Devin-->>Backend: status, messages, analysis
        Backend-->>Frontend: Session status

        alt Session completed
            Frontend->>Frontend: Hide loading, show analysis
        else Session still running
            Frontend->>Frontend: Continue showing loading
        end
    end
```

## Technical Implementation

### Backend

#### FastAPI Application (main.py)

**Core Features:**
- Async/await for non-blocking I/O
- CORS middleware for cross-origin requests
- In-memory result caching (session-scoped)
- Comprehensive error handling with HTTPException
- Structured logging for debugging

**Key Design Decisions:**
1. **In-memory storage**: Fast access, acceptable for demo/single-instance deployment
2. **Static loading screens**: Simple polling for completion status (reliable and debuggable)
3. **Fallback analysis**: Heuristic-based responses when Devin API unavailable

**API Endpoints:**
```python
# Health & Configuration
GET  /                    # API info
GET  /health              # Health check with config validation

# GitHub Issues
GET  /api/issues          # List issues (state filter)
GET  /api/issues/{number} # Get specific issue with cached results

# Devin Analysis
POST /api/analyze/{number}  # Analyze issue (unified flag for analysis+impl)

# Devin Execution
POST /api/execute/{number}  # Implement previously analyzed issue

# Session Monitoring
GET  /api/sessions/{id}        # Get session status

# History
GET  /api/history         # All cached results
```

#### Configuration Management (config.py)

```python
class Settings:
    GITHUB_TOKEN: str          # Fine-grained PAT
    GITHUB_REPO: str           # Format: owner/repo
    DEVIN_API_KEY: str         # Devin API key
    FRONTEND_URL: str          # CORS origin

    @property
    def github_headers(self) -> dict
    @property
    def devin_headers(self) -> dict
    @property
    def repo_owner(self) -> str
    @property
    def repo_name(self) -> str
```

**Validation on Startup:**
- Checks all required environment variables present
- Validates GitHub token format
- Validates repository name format
- Returns configuration status in `/health` endpoint

#### GitHub Service (github_service.py)

**Capabilities:**
- Issue listing with state filtering (open/closed/all)
- Single issue retrieval
- Comment posting with markdown formatting
- Automatic pull request filtering (GitHub API returns PRs in issues endpoint)

**Authentication:**
- Personal Access Token via Authorization header
- Required permissions: repo, issues, pull_requests

**Error Handling:**
- Request exceptions caught and logged
- HTTP errors re-raised with context
- Invalid responses handled gracefully

**Comment Format:**
```markdown
**Devin AI Analysis**

**Summary:** {summary}

**Confidence Score:** {confidence}%

**Proposed Implementation Steps:**
1. {step1}
2. {step2}
...

{Additional sections: Complexity, Challenges, Success Criteria}

---
*This analysis was generated automatically by Devin AI*
*Session: {session_url}*
```

#### Devin Service (devin_service.py)

**Session Types:**

1. **Analysis Session**: Request structured analysis with confidence scoring
   - Timeout: 300 seconds (5 minutes)
   - Polling interval: 5 seconds
   - Output: JSON with summary, confidence, implementation_steps, complexity, challenges, success_criteria

2. **Unified Session**: Perform both analysis and implementation in single session
   - Timeout: 900 seconds (15 minutes)
   - Polling interval: 10 seconds
   - Output: Analysis + PR link extraction

3. **Execution Session**: Implement previously analyzed issue
   - Timeout: 600 seconds (10 minutes)
   - Polling interval: 5 seconds
   - Output: Implementation status + PR link

**Session Creation:**
```python
def create_analysis_session(issue_number: int, title: str, body: str, labels: list) -> dict:
    """
    Creates Devin session with structured JSON prompt requesting:
    - summary: One-sentence description
    - confidence: Float 0.0-1.0
    - implementation_steps: List of actionable steps
    - complexity: low/medium/high/very_high
    - potential_challenges: List of anticipated difficulties
    - success_criteria: List of measurable success indicators
    """
```

**Response Parsing Strategy:**

The service implements a multi-layered fallback approach to extract analysis from Devin's responses:

```mermaid
graph TD
    A[Receive Devin Response] --> B{JSON block found?}
    B -->|Yes| C[Parse JSON directly]
    B -->|No| D{Valid JSON object?}
    D -->|Yes| E[Parse as JSON]
    D -->|No| F[Text-based regex parsing]

    C --> G{Has required fields?}
    E --> G
    F --> G

    G -->|Yes| H[Return structured analysis]
    G -->|No| I{None values present?}
    I -->|Yes| J[Apply fallback steps]
    I -->|No| H

    J --> H

    style C fill:#50c878
    style E fill:#50c878
    style F fill:#f5a623
    style J fill:#ff6b6b
```

**Parsing Layers:**
1. **JSON Parsing**: Extracts ```json blocks or direct JSON objects
2. **Text Parsing**: Regex patterns for markdown sections (## Summary, ## Confidence Score, etc.)
3. **Phase Extraction**: Identifies "Phase N:" headers as high-level implementation steps
4. **Fallback Steps**: Default implementation steps if parsing fails

**Session Status Handling:**
- **Completion States**: completed, success, done, finished, blocked
- **Failure States**: failed, error, cancelled, canceled
- **Running States**: running, pending, in_progress, processing, claimed
- **Unknown States**: Logged as warnings, polling continues

**Polling Implementation:**
```python
def poll_session_status(session_id: str, max_wait: int = 300, poll_interval: int = 5) -> dict:
    """
    Polls Devin API until session completes or times out.
    Returns final session state with extracted messages.
    """
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = get_session_status(session_id)
        status = response.get("status") or response.get("status_enum")

        if status in COMPLETED_STATES:
            return extract_devin_response(response)
        elif status in FAILED_STATES:
            raise Exception(f"Session failed: {status}")

        time.sleep(poll_interval)

    return timeout_response(session_id)
```


**Fallback Analysis:**

When Devin API is unavailable or rate-limited, the service generates heuristic-based analysis:

```python
def generate_fallback_analysis(issue_number: int, title: str, labels: list) -> dict:
    """
    Heuristic confidence scoring:
    - bug/fix: 0.75 (usually well-defined)
    - feature/enhancement: 0.60 (requires more planning)
    - documentation: 0.85 (straightforward)
    - default: 0.65

    Generic implementation steps provided.
    """
```

### Frontend

#### Technology Stack

- **React 18**: Component-based UI with hooks
- **TypeScript**: Type safety across the codebase
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first styling
- **Axios**: HTTP client with interceptors
- **Polling**: Simple status checking every 5 seconds

#### State Management

**No global state library used.** The application uses local component state with prop drilling:

```typescript
// App.tsx
const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

// IssueList.tsx
const [issues, setIssues] = useState<GitHubIssue[]>([]);
const [filter, setFilter] = useState<'open' | 'closed' | 'all'>('open');

// IssueCard.tsx
const [analysis, setAnalysis] = useState<Analysis | null>(null);
const [execution, setExecution] = useState<Execution | null>(null);
const [isAnalyzing, setIsAnalyzing] = useState(false);
```

**Justification:** For this application size, local state is sufficient. Adding Redux/Zustand would be over-engineering.

#### Component Design

**IssueCard.tsx** - The most complex component

```typescript
interface IssueCardProps {
  issue: GitHubIssue;  // Full issue data from GitHub
}

// State Management
const [analysis, setAnalysis] = useState<Analysis | null>(issue.analysis);
const [execution, setExecution] = useState<Execution | null>(issue.execution);
const [isAnalyzing, setIsAnalyzing] = useState(false);
const [isExecuting, setIsExecuting] = useState(false);
const [error, setError] = useState<string | null>(null);

// Action Handlers
const handleAnalyze = async () => {
  setIsAnalyzing(true);
  const result = await api.analyzeIssue(issue.number, postComment=true);
  setAnalysis(result.analysis);
  setIsAnalyzing(false);
};

const handleImplement = async () => {
  setIsExecuting(true);
  const result = await api.executeIssue(issue.number);
  setExecution(result.execution);
  setIsExecuting(false);
};
```

**SimpleLoadingScreen.tsx** - Polling-based progress

```typescript
useEffect(() => {
  const pollInterval = setInterval(async () => {
    const sessionData = await api.getSessionStatus(sessionId);

    if (sessionData.status === 'completed') {
      // Extract PR link if present
      const prMatch = sessionData.output?.match(/pull\/(\d+)/);
      if (prMatch) setPullRequestUrl(`https://github.com/${repo}/pull/${prMatch[1]}`);

      setIsComplete(true);
      clearInterval(pollInterval);
      onComplete?.();
    }
  }, 5000); // Poll every 5 seconds

  return () => clearInterval(pollInterval);
}, [sessionId]);
```


**ConfidenceBar.tsx** - Visual confidence display

```typescript
// Color coding based on confidence percentage
const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.7) return 'bg-green-500';   // High confidence
  if (confidence >= 0.4) return 'bg-yellow-500';  // Moderate confidence
  return 'bg-red-500';                             // Low confidence
};

const getConfidenceLabel = (confidence: number): string => {
  if (confidence >= 0.85) return 'Very High';
  if (confidence >= 0.7) return 'High';
  if (confidence >= 0.5) return 'Moderate';
  if (confidence >= 0.3) return 'Low';
  return 'Very Low';
};
```

#### API Client (services/api.ts)

**Configuration:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

**TypeScript Interfaces:**
```typescript
interface GitHubIssue {
  number: number;
  title: string;
  body: string;
  state: string;
  labels: Array<{ name: string; color: string }>;
  user: { login: string; avatar_url: string };
  created_at: string;
  html_url: string;
  analysis?: Analysis;    // Cached from backend
  execution?: Execution;  // Cached from backend
}

interface Analysis {
  session_id: string;
  summary: string;
  confidence: number;
  steps: string[];
  complexity?: string;
  challenges?: string[];
  success_criteria?: string[];
  status: string;
}

interface Execution {
  session_id: string;
  status: string;
  message: string;
  session_url: string;
}
```


### Integration Layer

#### GitHub API Integration

**Endpoints Used:**
- `GET /repos/{owner}/{repo}/issues` - List issues
- `GET /repos/{owner}/{repo}/issues/{number}` - Get issue details
- `POST /repos/{owner}/{repo}/issues/{number}/comments` - Post comments

**Authentication:**
```http
Authorization: token ghp_xxxxxxxxxxxxxxxxxxxxx
Accept: application/vnd.github.v3+json
```

**Required Token Permissions:**
- Repository: Issues (Read and Write)
- Repository: Pull Requests (Read and Write)
- Repository: Contents (Read and Write)
- Repository: Metadata (Read-only, automatically included)

**Pull Request Filtering:**
```python
def list_issues(state: str = "open") -> list:
    response = requests.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues")
    issues = response.json()

    # GitHub API returns PRs in issues endpoint - filter them out
    return [issue for issue in issues if 'pull_request' not in issue]
```

#### Devin API Integration

**Base URL:** `https://api.devin.ai/v1`

**Authentication:**
```http
Authorization: Bearer devin_api_key_xxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

**Session Creation:**
```http
POST /v1/sessions
{
  "prompt": "Analyze this GitHub issue and provide a structured response...",
  "metadata": {
    "issue_number": 123,
    "type": "analysis"
  }
}
```

**Response Structure:**
```json
{
  "session_id": "session-abc123",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Session Status Polling:**
```http
GET /v1/sessions/{session_id}?include_messages=true&include_thinking=true
```

**Response Fields (multiple possible locations):**
- `session.output` - Primary response location
- `session.response` - Alternative location
- `session.message` - Single message field
- `session.messages[]` - Array of message objects
- `session.text` - Plain text output
- `session.content` - Content field

**Session ID Extraction:**

Devin API returns session ID in different fields depending on context:
```python
def extract_session_id(response: dict) -> str:
    possible_fields = [
        'session_id',
        'sessionId',
        'id',
        'session',
        'devin_session_id'
    ]

    for field in possible_fields:
        if field in response and response[field]:
            return response[field]

    # Log all fields for debugging
    logger.error(f"Could not find session ID. Available fields: {response.keys()}")
    raise ValueError("No session ID found in response")
```

**Status Normalization:**

Devin uses both `status` and `status_enum` fields:
```python
def get_normalized_status(session_data: dict) -> str:
    return session_data.get("status") or session_data.get("status_enum") or "unknown"
```

## API Reference

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "configured": true,
  "github_repo": "owner/repository",
  "github_token_present": true,
  "devin_api_key_present": true
}
```

### List Issues

```http
GET /api/issues?state=open
```

**Query Parameters:**
- `state`: `open` | `closed` | `all` (default: `open`)

**Response:**
```json
[
  {
    "number": 123,
    "title": "Fix login validation bug",
    "body": "Users are unable to log in with special characters...",
    "state": "open",
    "labels": [{"name": "bug", "color": "d73a4a"}],
    "user": {"login": "johndoe", "avatar_url": "https://..."},
    "created_at": "2024-01-15T10:00:00Z",
    "html_url": "https://github.com/owner/repo/issues/123",
    "analysis": { /* if cached */ },
    "execution": { /* if cached */ }
  }
]
```

### Get Single Issue

```http
GET /api/issues/{issue_number}
```

**Response:**
```json
{
  "number": 123,
  "title": "Fix login validation bug",
  "body": "...",
  "state": "open",
  "labels": [...],
  "analysis": {
    "session_id": "session-abc123",
    "summary": "Fix email validation regex in authentication module",
    "confidence": 0.85,
    "steps": [
      "Review current email validation logic in auth/validators.py",
      "Update regex pattern to handle special characters",
      "Add unit tests for edge cases",
      "Update documentation"
    ],
    "complexity": "low",
    "challenges": [
      "Ensuring backward compatibility with existing users"
    ],
    "success_criteria": [
      "All special character emails accepted",
      "Existing tests still pass",
      "No security vulnerabilities introduced"
    ],
    "status": "completed"
  },
  "execution": {
    "session_id": "exec-xyz789",
    "status": "running",
    "message": "Execution started for issue #123",
    "session_url": "https://app.devin.ai/sessions/exec-xyz789"
  }
}
```

### Analyze Issue

```http
POST /api/analyze/{issue_number}?post_comment=true&unified=false
```

**Query Parameters:**
- `post_comment`: `true` | `false` (default: `true`) - Auto-post analysis as GitHub comment
- `unified`: `true` | `false` (default: `false`) - Perform both analysis + implementation

**Response (Analysis Only):**
```json
{
  "success": true,
  "issue_number": 123,
  "analysis": {
    "session_id": "session-abc123",
    "summary": "Fix email validation regex in authentication module",
    "confidence": 0.85,
    "steps": [...],
    "complexity": "low",
    "challenges": [...],
    "success_criteria": [...],
    "status": "completed"
  }
}
```

**Response (Unified Analysis + Implementation):**
```json
{
  "success": true,
  "issue_number": 123,
  "analysis": {
    "session_id": "unified-session-123",
    "summary": "...",
    "confidence": 0.85,
    "steps": [...],
    "status": "completed"
  },
  "execution": {
    "session_id": "unified-session-123",
    "status": "completed",
    "message": "Implementation completed. PR created: #45",
    "session_url": "https://app.devin.ai/sessions/unified-session-123",
    "pull_request": {
      "number": 45,
      "url": "https://github.com/owner/repo/pull/45"
    }
  }
}
```

### Execute Solution

```http
POST /api/execute/{issue_number}
```

**Response:**
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

**Response:**
```json
{
  "session_id": "session-abc123",
  "status": "completed",
  "messages": [
    {
      "id": "msg-1",
      "type": "devin_message",
      "content": "I've analyzed the issue..."
    }
  ],
  "thinking_steps": [
    {
      "id": "think-1",
      "content": "First, I'll review the current validation logic..."
    }
  ],
  "output": "Completed analysis with high confidence.",
  "session_url": "https://app.devin.ai/sessions/session-abc123"
}
```

### View History

```http
GET /api/history
```

**Response:**
```json
{
  "123": {
    "analysis": {...},
    "execution": {...}
  },
  "124": {
    "analysis": {...}
  }
}
```

## Setup & Deployment

### Prerequisites

- **Python 3.11+** (Backend)
- **Node.js 20+** (Frontend)
- **Docker & Docker Compose** (Optional, for containerized deployment)
- **GitHub Personal Access Token** with repo, issues, pull_requests permissions
- **Devin API Key**

### Option 1: Docker Compose (Recommended)

1. **Clone and configure:**
```bash
git clone <repository-url>
cd take-home

# Copy environment template
cp env.example .env

# Edit .env with your credentials
nano .env  # or your preferred editor
```

2. **Configure environment variables in `.env`:**
```env
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_REPO=owner/repository-name
DEVIN_API_KEY=your_devin_api_key_here
FRONTEND_URL=http://localhost:5173
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

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Yes | `ghp_abc123...` |
| `GITHUB_REPO` | Repository in `owner/repo` format | Yes | `octocat/hello-world` |
| `DEVIN_API_KEY` | Devin API key | Yes | `devin_key_xyz...` |
| `FRONTEND_URL` | Frontend URL for CORS | No | `http://localhost:5173` |
| `BACKEND_PORT` | Backend port | No | `8000` |
| `VITE_API_URL` | Backend API URL (frontend) | No | `http://localhost:8000/api` |

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Select repository access and grant these permissions:
   - **Repository permissions:**
     - Issues: Read and write
     - Pull requests: Read and write
     - Contents: Read and write
     - Metadata: Read-only (automatically included)
4. Copy the token to your `.env` file

### Devin API Key Setup

1. Access your Devin account at https://app.devin.ai
2. Navigate to API settings
3. Generate or copy your API key
4. Add it to your `.env` file

## Usage Guide

### 1. View Issues

When you open the application, it automatically fetches and displays all open issues from your configured repository.

**Features:**
- Filter by state (Open, Closed, All)
- View issue details, labels, and metadata
- Direct links to GitHub
- Cached analysis/execution results if available

### 2. Analyze an Issue

Click the **"Analyze with Devin"** button on any issue card.

**What happens:**
1. Frontend sends POST request to `/api/analyze/{issue_number}`
2. Backend fetches issue details from GitHub
3. Backend creates Devin session with structured analysis prompt
4. Backend polls Devin API every 5 seconds (max 5 minutes)
5. Backend parses response (JSON or text fallback)
6. Backend posts analysis as GitHub comment (if enabled)
7. Frontend displays analysis in AnalysisPanel

**Analysis includes:**
- **Summary**: One-sentence description of the issue
- **Confidence Score**: 0-100% likelihood of successful implementation
- **Implementation Steps**: Ordered list of actionable tasks
- **Complexity**: low/medium/high/very_high
- **Potential Challenges**: Anticipated difficulties
- **Success Criteria**: Measurable success indicators

**Confidence Levels:**
- **70-100%**: High confidence - straightforward implementation
- **40-69%**: Moderate confidence - may require investigation
- **0-39%**: Low confidence - complex or unclear requirements

### 3. Execute the Plan

After analysis, click **"Implement Plan"** to have Devin execute the solution.

**What happens:**
1. Frontend sends POST request to `/api/execute/{issue_number}`
2. Backend creates Devin execution session with implementation prompt
3. Devin autonomously:
   - Clones the repository
   - Makes code changes according to implementation plan
   - Runs tests
   - Creates a Pull Request (if configured)
4. Backend polls for completion
5. Backend extracts PR URL from response
6. Frontend displays execution status and PR link

### 4. Unified Analysis + Implementation

For faster workflow, use **"Analyze & Implement"** button.

**What happens:**
1. Single Devin session performs both analysis and implementation
2. Longer timeout: 15 minutes vs. 5 minutes for analysis only
3. Returns both analysis results and PR link
4. Automatically posts combined comment to GitHub issue

### 5. Track Progress

**Option 1: Polling (SimpleLoadingScreen)**
- Automatically polls session status every 5 seconds
- Displays type-specific messages (Analyzing, Executing, Implementing)
- Shows completion and PR link when done

**Option 2: External Monitoring**
- Click session URL to view progress in Devin dashboard
- Monitor Devin's terminal, file changes, and test execution
- View complete execution history

## Technical Deep Dives

### Response Parsing Strategy

One of the most complex aspects of the Devin integration is parsing responses, as Devin can return data in various formats. The implementation uses a multi-layered fallback approach:

**Layer 1: JSON Block Extraction**
```python
def extract_json_block(text: str) -> dict | None:
    """Extract JSON from ```json code blocks"""
    pattern = r'```json\s*(\{.*?\})\s*```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return None
```

**Layer 2: Direct JSON Parsing**
```python
def parse_as_json(text: str) -> dict | None:
    """Parse text as direct JSON object"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
```

**Layer 3: Text-based Regex Parsing**
```python
def parse_text_response(text: str) -> dict:
    """Extract sections using regex patterns"""
    summary = re.search(r'##\s*Summary\s*[:\-]?\s*(.+?)(?=##|\Z)', text, re.DOTALL)
    confidence = re.search(r'##\s*Confidence.*?(\d+(?:\.\d+)?)', text)
    steps = re.findall(r'^\d+\.\s*(.+)$', text, re.MULTILINE)

    return {
        "summary": summary.group(1).strip() if summary else None,
        "confidence": float(confidence.group(1)) / 100 if confidence else None,
        "implementation_steps": steps if steps else None
    }
```

**Layer 4: Phase Extraction**
```python
def extract_phases(text: str) -> list[str]:
    """Extract high-level phases instead of detailed sub-steps"""
    phase_pattern = r'(?:^|\n)(?:Phase\s+\d+|Step\s+\d+|###)\s*[:\-]?\s*(.+?)(?=\n|$)'
    phases = re.findall(phase_pattern, text, re.IGNORECASE)

    # Filter out sub-steps (e.g., "1.1", "a.", "  -")
    main_phases = [p.strip() for p in phases if not re.match(r'^\s*[\da-z]\.|^\s*[-*]', p)]

    return main_phases[:10]  # Limit to first 10 main phases
```

**Layer 5: Fallback Steps**
```python
def get_fallback_steps() -> list[str]:
    """Generic implementation steps when parsing fails"""
    return [
        "Analyze issue requirements and gather context",
        "Locate relevant code sections",
        "Implement the necessary changes",
        "Write or update tests",
        "Verify the solution addresses the issue",
        "Update documentation if needed"
    ]
```

### Session Status Management

Devin API uses multiple status formats. The application normalizes these:

```python
COMPLETED_STATES = {
    'completed', 'success', 'done', 'finished', 'blocked'
}

FAILED_STATES = {
    'failed', 'error', 'cancelled', 'canceled'
}

RUNNING_STATES = {
    'running', 'pending', 'in_progress', 'processing', 'claimed'
}

def get_session_status_category(status: str) -> str:
    """Normalize status to category"""
    status_lower = status.lower()

    if status_lower in COMPLETED_STATES:
        return 'completed'
    elif status_lower in FAILED_STATES:
        return 'failed'
    elif status_lower in RUNNING_STATES:
        return 'running'
    else:
        logger.warning(f"Unknown status: {status}")
        return 'running'  # Default to running to continue polling
```

### In-Memory Caching Strategy

The application uses a simple in-memory dictionary for result caching:

```python
# Global cache (session-scoped)
issue_results: Dict[int, Dict[str, Any]] = {}

def cache_analysis(issue_number: int, analysis: dict):
    if issue_number not in issue_results:
        issue_results[issue_number] = {}
    issue_results[issue_number]['analysis'] = analysis

def cache_execution(issue_number: int, execution: dict):
    if issue_number not in issue_results:
        issue_results[issue_number] = {}
    issue_results[issue_number]['execution'] = execution

def get_cached_results(issue_number: int) -> dict:
    return issue_results.get(issue_number, {})
```

**Trade-offs:**
- **Pros**: Fast, simple, no external dependencies
- **Cons**: Data lost on restart, not suitable for multi-instance deployment

**Production Alternative:**
```python
# Redis-based caching for production
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

def cache_analysis(issue_number: int, analysis: dict):
    cache.setex(
        f"issue:{issue_number}:analysis",
        3600,  # 1 hour TTL
        json.dumps(analysis)
    )
```

### Loading Screen Design

The application uses a simple, reliable polling approach:

**SimpleLoadingScreen Features:**
- **Static loading UI**: Shows animated loading indicators and informative messages  
- **Polling**: Checks session status every 5 seconds until completion
- **Smart completion**: Detects when Devin is done and shows results
- **Error handling**: Displays helpful error messages if something goes wrong
- **Type-aware messaging**: Different messages for analysis vs execution vs unified tasks
- **Completion screens**: Success screens with PR links for implementations

**Benefits:**
- Simple and reliable - no connection management complexity
- Works everywhere - no SSE/firewall concerns  
- Easy to debug - straightforward request/response cycle
- Good UX - informative loading states and smooth completion transitions

### Error Handling Philosophy

The application implements defensive error handling with graceful degradation:

**Principle 1: Never Fail Silently**
```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

**Principle 2: Provide Fallbacks**
```python
try:
    analysis = devin_service.analyze_issue(issue_number)
except DevinAPIError:
    analysis = generate_fallback_analysis(issue_number)
    analysis['note'] = 'Devin API unavailable. Heuristic analysis provided.'
```

**Principle 3: Log for Debugging**
```python
logger.info(f"Creating analysis session for issue #{issue_number}")
logger.debug(f"Session response: {response}")
logger.error(f"Session creation failed: {error}", exc_info=True)
```

**Principle 4: Inform the User**
```typescript
try {
  const result = await api.analyzeIssue(issueNumber);
  setAnalysis(result.analysis);
} catch (error) {
  setError('Failed to analyze issue. Please try again.');
  console.error('Analysis error:', error);
}
```

### Performance Considerations

**Backend:**
- Async/await for non-blocking I/O (FastAPI)
- Connection pooling for GitHub/Devin API calls
- In-memory caching to avoid redundant API calls
- Configurable polling intervals based on session type

**Frontend:**
- React.memo for expensive components (not currently used, but recommended for scaling)
- Debouncing for user inputs (not currently needed, but useful for search)
- Lazy loading for large issue lists (not implemented, suitable for 100+ issues)
- Polling cleanup on component unmount (prevents memory leaks)

**API Rate Limiting:**
- GitHub: 5000 requests/hour (authenticated)
- Devin: Variable based on plan (fallback analysis on rate limit)

**Optimization Opportunities:**
- Add Redis for persistent caching
- Implement WebSocket for bi-directional communication (if real-time features needed)
- Add pagination for issue lists (currently loads all at once)
- Implement request debouncing on frontend
- Add service worker for offline support

## Project Structure

```
take-home/
├── backend/                  # FastAPI backend
│   ├── main.py              # Main FastAPI application, API endpoints
│   ├── config.py            # Configuration management, environment variables
│   ├── github_service.py    # GitHub API integration (issues, comments)
│   ├── devin_service.py     # Devin API integration (sessions, polling, parsing)
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend Docker configuration
│
├── frontend/                # React + TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Header.tsx              # Repository header
│   │   │   ├── IssueList.tsx           # Issue list with filtering
│   │   │   ├── IssueCard.tsx           # Individual issue display
│   │   │   ├── AnalysisPanel.tsx       # Analysis results display
│   │   │   ├── ConfidenceBar.tsx       # Visual confidence indicator
│   │   │   └── SimpleLoadingScreen.tsx # Static loading screen with polling
│   │   ├── services/
│   │   │   └── api.ts       # API client with TypeScript interfaces
│   │   ├── App.tsx          # Root component, health check
│   │   ├── main.tsx         # Entry point
│   │   └── index.css        # Global styles (Tailwind)
│   ├── package.json         # Node dependencies
│   ├── vite.config.ts       # Vite configuration
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   ├── tsconfig.json        # TypeScript configuration
│   └── Dockerfile           # Frontend Docker configuration
│
├── docker-compose.yml       # Docker Compose configuration
├── env.example              # Environment variable template
├── run-local.sh             # Local run script (Linux/Mac)
├── run-local.bat            # Local run script (Windows)
├── run-docker.sh            # Docker run script
├── README.md                # This file
├── DEMO_SCRIPT.md           # Demo presentation guide
└── .gitignore               # Git ignore rules
```

## Security Considerations

- **Environment Variables**: All sensitive credentials stored in `.env`, not committed to git
- **Token Validation**: GitHub and Devin tokens validated on startup
- **CORS Protection**: Only specified origins allowed (localhost + FRONTEND_URL)
- **Input Validation**: Pydantic models for request validation
- **Error Messages**: No sensitive information leaked in error responses
- **HTTPS**: Use HTTPS in production (current setup is HTTP for local dev)
- **Rate Limiting**: Consider adding rate limiting for production (e.g., slowapi)
- **Secrets Management**: Use AWS Secrets Manager, HashiCorp Vault, or similar in production

## Troubleshooting

### Backend won't start
- Verify Python 3.11+ is installed: `python --version`
- Check all environment variables are set in `.env`
- Ensure GitHub token has correct permissions
- Check if port 8000 is available: `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr :8000` (Windows)

### Frontend won't start
- Verify Node.js 20+ is installed: `node --version`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check if port 5173 is available
- Clear Vite cache: `rm -rf frontend/.vite`

### Issues not loading
- Verify `GITHUB_REPO` format is `owner/repo`
- Check GitHub token has access to the repository
- Review backend logs for API errors: GitHub rate limiting or authentication failures
- Test GitHub API directly: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/repos/owner/repo/issues`

### Devin analysis fails
- Verify `DEVIN_API_KEY` is correct
- Check Devin API quota/limits in dashboard
- Review backend logs for API errors
- Fallback analysis will be used automatically on failure
- Test Devin API directly with curl

### CORS errors
- Ensure backend is running on port 8000
- Check frontend proxy configuration in `vite.config.ts`
- Verify CORS origins in `backend/main.py`
- Clear browser cache and hard reload

### Loading screen not updating
- Check that the session ID is valid
- Verify the backend `/api/sessions/{id}` endpoint is accessible
- Check browser console for any JavaScript errors
- Ensure polling is not blocked by network settings

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
docker-compose -f docker-compose.prod.yml up -d --build
```

**Option 2: Cloud Platforms**
- **Backend**: Deploy to AWS Lambda, Google Cloud Run, or Azure Functions
- **Frontend**: Deploy to Vercel, Netlify, or AWS S3 + CloudFront
- **Database**: Add PostgreSQL or Redis for persistent storage

**Option 3: Traditional Hosting**
- Build frontend: `cd frontend && npm run build`
- Serve frontend with nginx or Apache
- Run backend with gunicorn: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`

### Production Checklist

- [ ] Environment variables configured securely
- [ ] HTTPS enabled with valid SSL certificate
- [ ] CORS configured for production domain only
- [ ] Rate limiting implemented (e.g., slowapi)
- [ ] Database persistence (PostgreSQL, Redis)
- [ ] Logging configured (structured JSON logs)
- [ ] Monitoring and alerting (Sentry, DataDog, etc.)
- [ ] Backup and disaster recovery plan
- [ ] CI/CD pipeline configured
- [ ] Load balancing for multiple instances
- [ ] Health check endpoints monitored
- [ ] API documentation updated and accessible

## Monitoring

Access FastAPI's built-in documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Backend logs all API calls and errors to console.

## Future Enhancements

### High Priority
1. **Database Persistence**: PostgreSQL or MongoDB for analysis/execution history
2. **User Authentication**: Multi-user support with GitHub OAuth
3. **Webhook Integration**: Real-time updates via GitHub/Devin webhooks instead of polling
4. **Comprehensive Testing**: Unit tests, integration tests, E2E tests

### Medium Priority
5. **Batch Processing**: Analyze multiple issues concurrently
6. **Issue Prioritization**: Auto-prioritize based on confidence scores and labels
7. **Slack/Discord Integration**: Notifications for completed analyses
8. **Analytics Dashboard**: Metrics on analysis accuracy, execution success rate

### Low Priority
9. **Custom Devin Prompts**: User-configurable analysis prompts
10. **Issue Templates**: Pre-defined templates for common issue types
11. **Multi-Repository Support**: Switch between repositories in UI
12. **AI Model Selection**: Choose between different AI models

---
