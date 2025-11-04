from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import logging
import json
import asyncio
import time
from github_service import github_service
from devin_service import devin_service
from config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Devin Issue Assistant",
    description="Analyze and execute GitHub issues using Devin AI",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for analysis results
issue_results: Dict[int, Dict[str, Any]] = {}

# Pydantic models
class AnalysisResult(BaseModel):
    session_id: str
    summary: str
    confidence: float
    steps: List[str]
    status: str

class ExecutionResult(BaseModel):
    session_id: str
    status: str
    message: str
    session_url: Optional[str] = None

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Devin Issue Assistant API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    config_status = {
        "github_token": bool(settings.github_token),
        "github_repo": bool(settings.github_repo),
        "devin_api_key": bool(settings.devin_api_key),
    }
    
    all_configured = all(config_status.values())
    
    return {
        "status": "healthy" if all_configured else "misconfigured",
        "configuration": config_status,
        "repo": settings.github_repo if all_configured else None
    }

# GitHub Issues endpoints
@app.get("/api/issues")
async def list_issues(state: str = "open"):
    """
    List GitHub issues from the configured repository
    
    Args:
        state: Issue state (open, closed, all)
    """
    try:
        logger.info(f"Fetching {state} issues")
        issues = github_service.get_issues(state=state)
        
        # Enrich with cached analysis if available
        for issue in issues:
            issue_number = issue["number"]
            if issue_number in issue_results:
                issue["analysis"] = issue_results[issue_number].get("analysis")
                issue["execution"] = issue_results[issue_number].get("execution")
        
        return {
            "success": True,
            "count": len(issues),
            "issues": issues
        }
    except Exception as e:
        logger.error(f"Error fetching issues: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/issues/{issue_number}")
async def get_issue(issue_number: int):
    """
    Get a specific GitHub issue
    
    Args:
        issue_number: The issue number
    """
    try:
        logger.info(f"Fetching issue #{issue_number}")
        issue = github_service.get_issue(issue_number)
        
        # Add cached results if available
        if issue_number in issue_results:
            issue["analysis"] = issue_results[issue_number].get("analysis")
            issue["execution"] = issue_results[issue_number].get("execution")
        
        return {
            "success": True,
            "issue": issue
        }
    except Exception as e:
        logger.error(f"Error fetching issue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Analysis endpoints
@app.post("/api/analyze/{issue_number}")
async def analyze_issue(issue_number: int, post_comment: bool = True, unified: bool = False):
    """
    Analyze a GitHub issue using Devin AI - Synchronous, no streaming
    
    Args:
        issue_number: The issue number to analyze
        post_comment: Whether to post the analysis as a comment on GitHub
        unified: If True, performs both analysis and implementation in one session
    """
    try:
        session_type = "unified analysis+implementation" if unified else "analysis"
        logger.info(f"Starting synchronous {session_type} for issue #{issue_number}")
        
        # Fetch the issue
        issue = github_service.get_issue(issue_number)
        
        # Create Devin session - unified or analysis-only
        if unified:
            analysis = devin_service.create_unified_session(issue)
        else:
            analysis = devin_service.create_analysis_session(issue)
        
        # Store the result
        if issue_number not in issue_results:
            issue_results[issue_number] = {}
        issue_results[issue_number]["analysis"] = analysis
        issue_results[issue_number]["issue"] = issue

        logger.info(f"Analysis completed for issue #{issue_number}:")
        logger.info(f"  - Status: {analysis.get('status')}")
        logger.info(f"  - Summary length: {len(analysis.get('summary', '')) if analysis.get('summary') else 0}")
        logger.info(f"  - Confidence: {analysis.get('confidence')}")
        logger.info(f"  - post_comment parameter: {post_comment}")
        
        # Safe steps count - handle None case
        steps = analysis.get('steps', [])
        steps_count = len(steps) if steps is not None else 0
        logger.info(f"  - Steps count: {steps_count}")
        
        # Always include session_url for debugging if available
        if "session_id" in analysis and analysis["session_id"] != "fallback-session":
            analysis["session_url"] = f"https://app.devin.ai/sessions/{analysis['session_id']}"

        # Post comment to GitHub if requested
        # Accept multiple completion status values from both status and status_enum fields
        completed_statuses = {"completed", "success", "done", "finished", "blocked"}
        analysis_status = analysis.get("status", "").lower()
        analysis_status_enum = analysis.get("status_enum", "").lower()
        
        # Check both status and status_enum fields (Devin uses status_enum for more detailed status)
        is_completed = (analysis_status in completed_statuses or 
                       analysis_status_enum in completed_statuses)
        
        if post_comment and is_completed:
            try:
                comment = github_service.format_analysis_comment(analysis)
                github_service.post_comment(issue_number, comment)
                logger.info(f"Posted analysis comment to issue #{issue_number} (status: {analysis_status}, status_enum: {analysis_status_enum})")
            except Exception as e:
                logger.warning(f"Failed to post comment: {str(e)}")
        elif post_comment:
            logger.info(f"Skipping comment post for issue #{issue_number} - status '{analysis_status}' and status_enum '{analysis_status_enum}' not in completed statuses: {completed_statuses}")

        logger.info(f"Returning complete analysis response for issue #{issue_number}")
        return {
            "success": True,
            "issue_number": issue_number,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing issue #{issue_number}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Execution endpoints
@app.post("/api/execute/{issue_number}")
async def execute_issue(issue_number: int):
    """
    Execute the implementation plan for a GitHub issue using Devin AI
    
    Args:
        issue_number: The issue number to execute
    """
    try:
        logger.info(f"Starting execution for issue #{issue_number}")
        
        # Check if we have an analysis for this issue
        if issue_number not in issue_results or "analysis" not in issue_results[issue_number]:
            raise HTTPException(
                status_code=400,
                detail="Please analyze the issue first before executing"
            )
        
        issue = issue_results[issue_number]["issue"]
        analysis = issue_results[issue_number]["analysis"]
        
        # Create Devin execution session
        execution = devin_service.create_execution_session(issue, analysis)
        
        # Store the result
        issue_results[issue_number]["execution"] = execution
        
        return {
            "success": True,
            "issue_number": issue_number,
            "execution": execution
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing issue #{issue_number}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Session status endpoint
@app.get("/api/sessions/{session_id}")
async def get_session_status(session_id: str):
    """
    Get the status of a Devin session
    
    Args:
        session_id: The Devin session ID
    """
    try:
        status = devin_service.get_session_status(session_id)
        return {
            "success": True,
            "session": status
        }
    except Exception as e:
        logger.error(f"Error fetching session status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Session streaming endpoint
@app.get("/api/sessions/{session_id}/stream")
async def stream_session_updates(session_id: str):
    """
    Stream real-time updates from a Devin session using Server-Sent Events
    
    Args:
        session_id: The Devin session ID
    """
    async def generate_session_stream():
        """Generate SSE stream of session updates"""
        logger.info(f"Starting stream for session {session_id}")
        
        last_message_count = 0
        last_thinking_count = 0
        session_completed = False
        
        try:
            while not session_completed:
                try:
                    # Get detailed session information
                    session_details = devin_service.get_session_details(session_id)
                    
                    status = session_details.get("status", "unknown")
                    status_enum = session_details.get("status_enum", "")
                    messages = session_details.get("messages", [])
                    thinking_steps = session_details.get("thinking_steps", [])
                    
                    # Check if session is completed
                    if (status in ["completed", "success", "done", "finished", "failed", "error", "cancelled", "canceled"] or 
                        status_enum in ["completed", "success", "done", "finished", "blocked", "failed", "error", "cancelled", "canceled"]):
                        session_completed = True
                    
                    # Send new messages with pacing
                    if messages and len(messages) > last_message_count:
                        new_messages = messages[last_message_count:]
                        for message in new_messages:
                            data = {
                                "type": "message",
                                "data": message,
                                "timestamp": time.time()
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                            
                            # Add delay between messages for better streaming experience
                            await asyncio.sleep(0.3)
                        last_message_count = len(messages) if messages else 0
                    
                    # Send new thinking steps with artificial pacing for better UX
                    if thinking_steps and len(thinking_steps) > last_thinking_count:
                        new_thinking = thinking_steps[last_thinking_count:]
                        for step in new_thinking:
                            data = {
                                "type": "thinking",
                                "data": step,
                                "timestamp": time.time()
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                            
                            # Add small delay between thinking steps for better streaming experience
                            await asyncio.sleep(0.5)
                        last_thinking_count = len(thinking_steps) if thinking_steps else 0
                    
                    # Send status update
                    status_data = {
                        "type": "status",
                        "data": {
                            "status": status,
                            "status_enum": status_enum,
                            "message_count": len(messages) if messages else 0,
                            "thinking_count": len(thinking_steps) if thinking_steps else 0,
                            "completed": session_completed
                        },
                        "timestamp": time.time()
                    }
                    yield f"data: {json.dumps(status_data)}\n\n"
                    
                    if session_completed:
                        # Re-parse the session to get final analysis results
                        try:
                            # Find the issue that this session belongs to and re-parse
                            session_to_reparse = None
                            issue_num_to_update = None
                            for issue_num, data in issue_results.items():
                                analysis = data.get("analysis", {})
                                if analysis.get("session_id") == session_id:
                                    session_to_reparse = session_details
                                    issue_num_to_update = issue_num
                                    break
                            
                            if session_to_reparse and issue_num_to_update:
                                # Re-parse with the completed session data
                                issue = issue_results[issue_num_to_update]["issue"]
                                updated_analysis = devin_service._parse_analysis_result(
                                    session_to_reparse, session_id, issue
                                )
                                updated_analysis["status"] = "completed"  # Mark as completed
                                
                                # Update stored analysis
                                issue_results[issue_num_to_update]["analysis"] = updated_analysis
                                logger.info(f"Updated analysis for issue #{issue_num_to_update} with final results")
                                
                                # Post comment to GitHub for streaming completed analysis
                                # Check if the updated analysis should trigger a comment
                                completed_statuses = {"completed", "success", "done", "finished", "blocked"}
                                analysis_status = updated_analysis.get("status", "").lower()
                                analysis_status_enum = updated_analysis.get("status_enum", "").lower()
                                is_completed = (analysis_status in completed_statuses or 
                                               analysis_status_enum in completed_statuses)
                                
                                if is_completed:
                                    try:
                                        comment = github_service.format_analysis_comment(updated_analysis)
                                        github_service.post_comment(issue_num_to_update, comment)
                                        logger.info(f"Posted streaming completion comment to issue #{issue_num_to_update} (status: {analysis_status}, status_enum: {analysis_status_enum})")
                                    except Exception as comment_error:
                                        logger.warning(f"Failed to post streaming completion comment: {str(comment_error)}")
                                else:
                                    logger.info(f"Skipping streaming comment post for issue #{issue_num_to_update} - status '{analysis_status}' and status_enum '{analysis_status_enum}' not in completed statuses: {completed_statuses}")
                                
                                # Send updated analysis in completion event
                                completion_data = {
                                    "type": "completed",  
                                    "data": {
                                        "session_id": session_id,
                                        "final_status": status,
                                        "final_status_enum": status_enum,
                                        "total_messages": len(messages) if messages else 0,
                                        "total_thinking_steps": len(thinking_steps) if thinking_steps else 0,
                                        "updated_analysis": {
                                            "summary": updated_analysis.get("summary", "")[:200] + "..." if len(updated_analysis.get("summary", "")) > 200 else updated_analysis.get("summary", ""),
                                            "confidence": updated_analysis.get("confidence"),
                                            "steps_count": len(updated_analysis.get("steps", []))
                                        }
                                    },
                                    "timestamp": time.time()
                                }
                            else:
                                # Fallback completion event
                                completion_data = {
                                    "type": "completed",
                                    "data": {
                                        "session_id": session_id,
                                        "final_status": status,
                                        "final_status_enum": status_enum,
                                        "total_messages": len(messages) if messages else 0,
                                        "total_thinking_steps": len(thinking_steps) if thinking_steps else 0
                                    },
                                    "timestamp": time.time()
                                }
                        except Exception as parse_error:
                            logger.error(f"Error re-parsing completed session: {str(parse_error)}")
                            # Send standard completion event
                            completion_data = {
                                "type": "completed",
                                "data": {
                                    "session_id": session_id,
                                    "final_status": status,
                                    "final_status_enum": status_enum,
                                    "total_messages": len(messages) if messages else 0,
                                    "total_thinking_steps": len(thinking_steps) if thinking_steps else 0
                                },
                                "timestamp": time.time()
                            }
                        
                        yield f"data: {json.dumps(completion_data)}\n\n"
                        logger.info(f"Session {session_id} completed, ending stream")
                        break
                    
                    # Use shorter polling interval for more responsive streaming
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in session stream: {str(e)}")
                    error_data = {
                        "type": "error",
                        "data": {
                            "error": str(e),
                            "session_id": session_id
                        },
                        "timestamp": time.time()
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    await asyncio.sleep(5)  # Wait longer on error
                    
        except Exception as e:
            logger.error(f"Fatal error in session stream: {str(e)}")
            final_error = {
                "type": "fatal_error",
                "data": {
                    "error": str(e),
                    "session_id": session_id
                },
                "timestamp": time.time()
            }
            yield f"data: {json.dumps(final_error)}\n\n"
    
    return StreamingResponse(
        generate_session_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

# Results history endpoint
@app.get("/api/history")
async def get_history():
    """
    Get analysis and execution history for all issues
    """
    history = []
    for issue_number, data in issue_results.items():
        history.append({
            "issue_number": issue_number,
            "issue_title": data.get("issue", {}).get("title", "Unknown"),
            "analysis": data.get("analysis"),
            "execution": data.get("execution")
        })
    
    return {
        "success": True,
        "count": len(history),
        "history": history
    }

