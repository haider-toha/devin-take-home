# Complete Setup Guide

This guide will walk you through setting up the Devin Issue Assistant from scratch.

## Step 1: Prerequisites Check

Before you begin, ensure you have:

### Required Software
- [ ] **Python 3.11 or higher**
  ```bash
  python --version  # Should show 3.11.x or higher
  ```

- [ ] **Node.js 20 or higher**
  ```bash
  node --version  # Should show 20.x.x or higher
  ```

- [ ] **npm** (comes with Node.js)
  ```bash
  npm --version
  ```

- [ ] **Git**
  ```bash
  git --version
  ```

### Optional (for Docker deployment)
- [ ] **Docker Desktop** or **Docker Engine**
  ```bash
  docker --version
  docker-compose --version
  ```

## Step 2: Get GitHub Personal Access Token

1. **Navigate to GitHub Settings:**
   - Go to https://github.com/settings/tokens
   - Click on "Fine-grained tokens" (recommended) or "Tokens (classic)"

2. **Create New Token:**
   - Click "Generate new token"
   - Give it a descriptive name (e.g., "Devin Issue Assistant")
   - Set expiration (90 days recommended for development)

3. **Set Permissions (Fine-grained token):**
   - **Repository access:** Select "Only select repositories" and choose your target repo
   - **Permissions:**
     - Issues: Read and write
     - Pull requests: Read and write
     - Contents: Read and write
     - Metadata: Read-only (auto-selected)

4. **Generate and Copy Token:**
   - Click "Generate token"
   - **IMPORTANT:** Copy the token immediately - you won't see it again!
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 3: Get Devin API Key

1. **Access Devin Dashboard:**
   - Go to https://app.devin.ai
   - Log in with your account

2. **Navigate to API Settings:**
   - Click on your profile/settings
   - Find "API Keys" or "Integrations" section

3. **Generate API Key:**
   - Click "Create new API key"
   - Copy the key
   - Format: Your Devin API key format

## Step 4: Choose Your Repository

Decide which GitHub repository to use:

### Option A: Use Existing Repository
```env
GITHUB_REPO=yourusername/your-existing-repo
```

### Option B: Create Test Repository
1. Go to https://github.com/new
2. Create a new repository (e.g., "devin-test-repo")
3. Add some test issues:
   - Click "Issues" tab
   - Create 2-3 sample issues with descriptions
   - Example: "Fix login validation bug", "Add dark mode feature"
4. Use format:
```env
GITHUB_REPO=yourusername/devin-test-repo
```

## Step 5: Project Setup

### 5.1 Clone Repository
```bash
# If from Git
git clone <repository-url>
cd take-home

# If from zip
unzip take-home.zip
cd take-home
```

### 5.2 Create Environment File
```bash
# Copy the template
cp env.example .env

# On Windows:
copy env.example .env
```

### 5.3 Edit `.env` File
Open `.env` in your favorite text editor and fill in:

```env
# GitHub Configuration
GITHUB_TOKEN=ghp_your_actual_github_token_here
GITHUB_REPO=owner/repository-name

# Devin API Configuration
DEVIN_API_KEY=your_actual_devin_api_key_here

# Backend Configuration (usually don't need to change)
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
```

**Example:**
```env
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz123
GITHUB_REPO=octocat/hello-world
DEVIN_API_KEY=sk_devin_abc123xyz789
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
```

## Step 6: Choose Installation Method

### Method 1: Quick Start with Docker (Recommended)

**Best for:** Clean, isolated environment

```bash
# Make script executable (Linux/Mac)
chmod +x run-docker.sh

# Run
./run-docker.sh

# On Windows, use:
docker-compose up --build
```

**Expected output:**
```
Creating network "take-home_default"
Building backend...
Building frontend...
Creating take-home_backend_1  ... done
Creating take-home_frontend_1 ... done
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Method 2: Local Development

**Best for:** Active development, debugging

#### Linux/Mac:
```bash
chmod +x run-local.sh
./run-local.sh
```

#### Windows:
```cmd
run-local.bat
```

#### Manual Steps:

**Terminal 1 - Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

## Step 7: Verify Installation

### 7.1 Check Backend Health
Open browser to: http://localhost:8000/health

**Expected response:**
```json
{
  "status": "healthy",
  "configuration": {
    "github_token": true,
    "github_repo": true,
    "devin_api_key": true
  },
  "repo": "owner/repository-name"
}
```

**If you see `"status": "misconfigured"`:**
- Check your `.env` file
- Verify all credentials are correct
- Restart the backend server

### 7.2 Check API Documentation
Open: http://localhost:8000/docs

You should see the FastAPI Swagger interface with all endpoints.

### 7.3 Check Frontend
Open: http://localhost:5173

**Expected:**
- Green "Connected" indicator in header
- Repository name displayed
- List of issues loading

**If you see "Backend Not Configured":**
- Backend is not running or misconfigured
- Check backend logs
- Verify `.env` file

## Step 8: Test the Application

### 8.1 View Issues
- Issues should load automatically
- Try filtering by "Open", "Closed", "All"

### 8.2 Analyze an Issue
1. Click "Analyze with Devin" on any issue
2. Wait for analysis (10-60 seconds)
3. Review the confidence score and implementation steps
4. Check GitHub - a comment should appear on the issue

### 8.3 Execute a Solution (Optional)
1. After analysis completes, click "Implement Plan"
2. Note the Devin session URL
3. Monitor progress in Devin dashboard

## Common Issues and Solutions

### Issue: Port Already in Use

**Error:** `Address already in use: 8000` or `5173`

**Solution:**
```bash
# Find process using port
# Linux/Mac:
lsof -i :8000
kill -9 <PID>

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: Python Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Make sure virtual environment is activated
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: GitHub API Rate Limit

**Error:** `API rate limit exceeded`

**Solution:**
- Wait an hour for rate limit reset
- Ensure you're using a token (higher limits)
- Check https://api.github.com/rate_limit

### Issue: CORS Error

**Error:** `Access to fetch blocked by CORS policy`

**Solution:**
1. Verify backend is running on port 8000
2. Check `backend/main.py` CORS configuration
3. Restart both frontend and backend

### Issue: Dependencies Installation Fails

**Python:**
```bash
# Upgrade pip first
pip install --upgrade pip
pip install -r requirements.txt
```

**Node.js:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Step 9: Development Tips

### Hot Reload
Both frontend and backend support hot reload:
- **Backend:** Changes to Python files auto-restart
- **Frontend:** Changes to React files auto-refresh browser

### Viewing Logs

**Backend:**
- Logs appear in terminal where backend is running
- Check for errors, API calls, etc.

**Frontend:**
- Open browser DevTools (F12)
- Check Console tab for errors
- Network tab for API calls

### Testing API Directly

Use the Swagger UI at http://localhost:8000/docs:
1. Click on any endpoint
2. Click "Try it out"
3. Fill in parameters
4. Click "Execute"

## Step 10: Stopping the Application

### Docker:
```bash
# Ctrl+C in terminal
# Then:
docker-compose down
```

### Local:
```bash
# Press Ctrl+C in each terminal (backend and frontend)
```

### Windows batch file:
```
# Press any key when prompted
```

## Next Steps

Application is running
Configuration verified
Test analysis completed

**You're ready to:**
1. Record your demo video
2. Test with real issues
3. Explore the API documentation
4. Customize the UI
5. Add additional features

## Need Help?

1. Check the main [README.md](README.md)
2. Review API docs at http://localhost:8000/docs
3. Check terminal logs for errors
4. Verify all credentials in `.env`

---

**Congratulations! Your Devin Issue Assistant is ready to use!**

