import requests
from typing import Dict, Any, Optional
import logging
import time
from config import settings

logger = logging.getLogger(__name__)

class DevinService:
    """Service for interacting with Devin API"""
    
    def __init__(self):
        self.base_url = settings.devin_api_base
        self.headers = settings.devin_headers
    
    def create_analysis_session(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Devin session to analyze a GitHub issue
        
        Args:
            issue: GitHub issue dictionary
            
        Returns:
            Analysis results including session ID, summary, confidence, and steps
        """
        try:
            issue_number = issue.get("number", "unknown")
            issue_title = issue.get("title", "")
            issue_body = issue.get("body", "")
            issue_labels = [label["name"] for label in issue.get("labels", [])]
            
            # Construct analysis prompt
            prompt = f"""Analyze this GitHub issue and provide:
1. A brief summary of what needs to be done
2. A confidence score (0.0 to 1.0) indicating how feasible this is to solve
3. A step-by-step implementation plan

GitHub Issue #{issue_number}:
Title: {issue_title}

Description:
{issue_body or 'No description provided'}

Labels: {', '.join(issue_labels) if issue_labels else 'None'}

Please respond with a structured analysis including confidence level and actionable steps."""

            payload = {
                "prompt": prompt,
                "metadata": {
                    "issue_number": issue_number,
                    "type": "analysis"
                }
            }
            
            logger.info(f"Creating Devin analysis session for issue #{issue_number}")
            response = requests.post(
                f"{self.base_url}/sessions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            session_data = response.json()
            logger.info(f"Devin API response: {session_data}")
            
            # Try to extract session ID from various possible fields
            session_id = session_data.get("id")
            logger.info(f"Tried 'id': {session_id}")
            if not session_id:
                session_id = session_data.get("session_id")
                logger.info(f"Tried 'session_id': {session_id}")
            if not session_id:
                session_id = session_data.get("sessionId")
                logger.info(f"Tried 'sessionId': {session_id}")
            if not session_id and isinstance(session_data.get("data"), dict):
                session_id = session_data.get("data", {}).get("id")
                logger.info(f"Tried nested 'data.id': {session_id}")
            
            if not session_id:
                logger.error(f"No session ID found in response: {session_data}")
                raise Exception(f"Devin API did not return a session ID: {session_data}")
            
            logger.info(f"Created session {session_id} for issue #{issue_number}")

            # Poll for results - wait longer for Devin to respond for complex issues
            try:
                result = self._wait_for_session_result(session_id, max_wait=300, interval=5)
                # Parse and structure the result
                analysis = self._parse_analysis_result(result, session_id, issue)
                return analysis
            except Exception as e:
                logger.warning(f"Error waiting for session result: {str(e)}")
                logger.info(f"Devin is still processing. Returning current session state.")

                # Get the latest session state even if not completed
                try:
                    partial_result = self.get_session_status(session_id)
                    # Try to parse whatever Devin has provided so far
                    return self._parse_analysis_result(partial_result, session_id, issue)
                except Exception as parse_error:
                    logger.error(f"Could not get session status: {str(parse_error)}")
                    # Last resort: return minimal info with session link
                    return {
                        "session_id": session_id,
                        "summary": f"Devin is still analyzing this issue. The analysis is taking longer than expected. Check the session for live updates.",
                        "confidence": self._calculate_confidence_heuristic(issue),
                        "steps": ["View the Devin session link below for real-time analysis progress"],
                        "status": "running",
                        "session_url": session_data.get("url", f"https://app.devin.ai/sessions/{session_id.replace('devin-', '')}")
                    }
            
        except requests.exceptions.HTTPError as e:
            # Handle rate limiting gracefully
            if e.response.status_code == 429:
                logger.warning(f"Devin API rate limit reached for issue #{issue.get('number', 'unknown')}")
                return self._create_fallback_analysis(issue, "API rate limit reached - please try again in a few minutes")
            else:
                logger.error(f"Error creating Devin analysis session: {str(e)}")
                return self._create_fallback_analysis(issue, str(e))
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Devin analysis session: {str(e)}")
            # Return a fallback analysis
            return self._create_fallback_analysis(issue, str(e))
    
    def create_execution_session(self, issue: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Devin session to execute the implementation plan

        Args:
            issue: GitHub issue dictionary
            analysis: Previous analysis results

        Returns:
            Execution results
        """
        try:
            issue_number = issue.get("number", "unknown")
            repo = settings.github_repo

            # Construct execution prompt
            prompt = f"""Implement the proposed fix for GitHub issue #{issue_number} in repository {repo}.

Issue Title: {issue.get('title', '')}

Implementation Plan:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(analysis.get('steps', [])))}

Please implement this solution and create a pull request with the changes. Include proper commit messages and PR description."""

            payload = {
                "prompt": prompt,
                "metadata": {
                    "issue_number": issue_number,
                    "type": "execution",
                    "analysis_session_id": analysis.get("session_id")
                }
            }

            logger.info(f"Creating Devin execution session for issue #{issue_number}")
            response = requests.post(
                f"{self.base_url}/sessions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

            session_data = response.json()
            logger.info(f"Devin API response: {session_data}")

            # Try to extract session ID from various possible fields
            session_id = session_data.get("id")
            if not session_id:
                session_id = session_data.get("session_id")
            if not session_id:
                session_id = session_data.get("sessionId")
            if not session_id and isinstance(session_data.get("data"), dict):
                session_id = session_data.get("data", {}).get("id")

            if not session_id:
                logger.error(f"No session ID found in response: {session_data}")
                raise Exception(f"Devin API did not return a session ID: {session_data}")

            logger.info(f"Created execution session {session_id} for issue #{issue_number}")

            return {
                "session_id": session_id,
                "status": session_data.get("status", "running"),
                "message": f"Execution started for issue #{issue_number}",
                "session_url": f"https://app.devin.ai/sessions/{session_id}"
            }

        except requests.exceptions.HTTPError as e:
            # Handle rate limiting gracefully
            if e.response.status_code == 429:
                logger.warning(f"Devin API rate limit reached for issue #{issue_number}")
                return self._create_fallback_execution(issue, analysis, "API rate limit reached")
            else:
                logger.error(f"Error creating Devin execution session: {str(e)}")
                return self._create_fallback_execution(issue, analysis, str(e))
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Devin execution session: {str(e)}")
            return self._create_fallback_execution(issue, analysis, str(e))
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the status of a Devin session
        
        Args:
            session_id: The session ID
            
        Returns:
            Session status information
        """
        try:
            logger.info(f"Fetching status for session {session_id}")
            response = requests.get(
                f"{self.base_url}/sessions/{session_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching session status: {str(e)}")
            raise Exception(f"Failed to get session status: {str(e)}")
    
    def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed session information including messages and progress
        
        Args:
            session_id: The session ID
            
        Returns:
            Detailed session information with messages, thinking steps, etc.
        """
        try:
            logger.debug(f"Fetching detailed session info for {session_id}")
            response = requests.get(
                f"{self.base_url}/sessions/{session_id}",
                headers=self.headers,
                params={"include_messages": True, "include_thinking": True}
            )
            response.raise_for_status()
            
            session_data = response.json()
            
            # Extract and format messages for streaming
            raw_messages = session_data.get("messages", [])
            formatted_messages = []
            thinking_steps = []
            
            for msg in raw_messages:
                if isinstance(msg, dict):
                    msg_type = msg.get("type", "")
                    msg_content = msg.get("message", "")
                    msg_timestamp = msg.get("timestamp", "")
                    
                    if msg_type == "devin_message" and msg_content:
                        # Check if this looks like a thinking step or a final response
                        if (len(msg_content) < 200 and 
                            any(keyword in msg_content.lower() for keyword in 
                                ["analyzing", "examining", "looking", "checking", "investigating"])):
                            # Short messages with analysis keywords are likely thinking steps
                            thinking_steps.append({
                                "content": msg_content,
                                "timestamp": msg_timestamp
                            })
                        else:
                            # Longer messages or final responses are treated as messages
                            formatted_messages.append({
                                "content": msg_content,
                                "role": "assistant",
                                "timestamp": msg_timestamp,
                                "type": "devin_response"
                            })
                    elif msg_type == "initial_user_message" and msg_content:
                        formatted_messages.append({
                            "content": msg_content,
                            "role": "user", 
                            "timestamp": msg_timestamp,
                            "type": "user_request"
                        })
            
            # If no thinking steps were identified but we have devin messages, 
            # use the shorter ones as thinking steps
            if not thinking_steps and len(formatted_messages) > 1:
                # Move shorter devin messages to thinking steps
                messages_to_keep = []
                for msg in formatted_messages:
                    if (msg["role"] == "assistant" and 
                        len(msg["content"]) < 300 and
                        msg != formatted_messages[-1]):  # Keep the last message as the main response
                        thinking_steps.append({
                            "content": msg["content"],
                            "timestamp": msg["timestamp"]
                        })
                    else:
                        messages_to_keep.append(msg)
                formatted_messages = messages_to_keep
            
            progress = session_data.get("progress", {})
            
            return {
                "session_id": session_id,
                "status": session_data.get("status", "unknown"),
                "status_enum": session_data.get("status_enum", ""),
                "messages": formatted_messages,
                "thinking_steps": thinking_steps,
                "progress": progress,
                "last_updated": session_data.get("updated_at", session_data.get("last_updated")),
                "raw_data": session_data  # For debugging
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching session details: {str(e)}")
            raise Exception(f"Failed to get session details: {str(e)}")
    
    def _wait_for_session_result(self, session_id: str, max_wait: int = 60, interval: int = 2) -> Dict[str, Any]:
        """
        Poll for session result with timeout

        Args:
            session_id: The session ID
            max_wait: Maximum wait time in seconds
            interval: Polling interval in seconds

        Returns:
            Session result
        """
        elapsed = 0
        poll_count = 0
        while elapsed < max_wait:
            poll_count += 1
            session = self.get_session_status(session_id)
            status = session.get("status", "unknown")
            status_enum = session.get("status_enum", "")

            logger.info(f"Poll #{poll_count} - Session {session_id} status: {status}, status_enum: {status_enum} (elapsed: {elapsed}s/{max_wait}s)")

            # Check for completion states
            if status in ["completed", "success", "done", "finished"] or status_enum in ["completed", "success", "done", "finished", "blocked"]:
                logger.info(f"Session {session_id} completed successfully after {elapsed}s (status: {status}, status_enum: {status_enum})")
                return session

            # Check for failure states
            elif status in ["failed", "error", "cancelled", "canceled"] or status_enum in ["failed", "error", "cancelled", "canceled"]:
                logger.error(f"Session {session_id} failed with status: {status}, status_enum: {status_enum}")
                raise Exception(f"Session failed with status: {status}")

            # For running/pending states, continue polling
            # "claimed" means Devin has claimed the session and is working on it
            elif status in ["running", "pending", "in_progress", "processing", "claimed"] or status_enum in ["working", "running", "pending", "in_progress", "processing"]:
                logger.debug(f"Session {session_id} still {status}/{status_enum}, continuing to poll...")

            # For unknown states, log a warning but continue
            else:
                logger.warning(f"Session {session_id} has unknown status: {status}, status_enum: {status_enum}. Will continue polling. If this persists, consider checking the Devin UI directly.")

            time.sleep(interval)
            elapsed += interval

        # Timeout reached - return current state
        final_session = self.get_session_status(session_id)
        final_status = final_session.get("status", "unknown")
        logger.warning(f"Session {session_id} timed out after {max_wait}s with status: {final_status}")
        logger.info(f"Returning partial result. Full session data: {final_session}")
        return final_session
    
    def _parse_devin_text_response(self, text: str) -> Dict[str, Any]:
        """
        Parse Devin's formatted text response to extract structured data

        Args:
            text: Devin's text response

        Returns:
            Parsed data with summary, confidence, and steps
        """
        import re

        parsed = {
            "summary": None,
            "confidence": None,
            "steps": []
        }

        # Extract confidence score
        # Patterns like "Confidence Score: 0.75" or "2. Confidence Score: 0.75"
        confidence_match = re.search(r'confidence\s*(?:score)?:?\s*(\d+\.?\d*)', text, re.IGNORECASE)
        if confidence_match:
            try:
                parsed["confidence"] = float(confidence_match.group(1))
                logger.info(f"Extracted confidence: {parsed['confidence']}")
            except ValueError:
                pass

        # Extract summary section
        # Look for "1. Summary" or "Summary" header followed by content
        summary_match = re.search(r'(?:^|\n)(?:\d+\.\s*)?summary[:\s]*\n(.+?)(?=\n\d+\.|$)', text, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(1).strip()
            # Take first paragraph or first 500 chars
            first_para = summary_text.split('\n\n')[0] if '\n\n' in summary_text else summary_text
            parsed["summary"] = first_para[:500].strip()
            logger.info(f"Extracted summary: {parsed['summary'][:100]}...")
        else:
            # Fallback: Look for any paragraph after the title
            lines = text.strip().split('\n')
            if len(lines) > 2:
                # Skip title/header lines and get first meaningful content
                for i, line in enumerate(lines[1:], 1):  # Skip first line
                    if line.strip() and not re.match(r'^\d+\.', line.strip()) and len(line.strip()) > 50:
                        parsed["summary"] = line.strip()
                        logger.info(f"Using fallback summary: {parsed['summary'][:100]}...")
                        break
                if not parsed["summary"] and len(text) > 100:
                    parsed["summary"] = text[:500].strip()

        # Extract steps from various formats
        # Pattern 1: "Phase N: Title" followed by substeps
        phase_matches = re.findall(r'Phase\s+\d+:\s*([^\n]+)', text, re.IGNORECASE)
        if phase_matches and len(phase_matches) >= 3:
            parsed["steps"] = phase_matches
            logger.info(f"Extracted {len(parsed['steps'])} steps from phases")
        else:
            # Pattern 2: Numbered list "1. Step" or "Step 1:"
            step_patterns = [
                r'(?:^|\n)(?:Step\s+)?(\d+)\.\s*([^\n]+)',  # "1. Step" or "Step 1. Description"
                r'(?:^|\n)-\s*([^\n]+)',  # "- Step"
            ]

            for pattern in step_patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                if matches and len(matches) >= 3:
                    if isinstance(matches[0], tuple):
                        # Extract description part (second group)
                        parsed["steps"] = [match[1] if len(match) > 1 else match[0] for match in matches]
                    else:
                        parsed["steps"] = matches
                    logger.info(f"Extracted {len(parsed['steps'])} steps using pattern")
                    break

        return parsed

    def _calculate_confidence_heuristic(self, issue: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on issue characteristics

        Args:
            issue: GitHub issue

        Returns:
            Confidence score (0.0 to 1.0)
        """
        title = issue.get("title", "").lower()
        labels = [label["name"].lower() for label in issue.get("labels", [])]

        # Default moderate confidence
        confidence = 0.65

        if "bug" in labels or "fix" in title:
            confidence = 0.75
        elif "feature" in labels or "enhancement" in labels:
            confidence = 0.60
        elif "documentation" in labels:
            confidence = 0.85

        return confidence

    def _parse_analysis_result(self, session: Dict[str, Any], session_id: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Devin session result into structured analysis

        Args:
            session: Session data from Devin API
            session_id: Session ID
            issue: GitHub issue (for heuristic fallback)

        Returns:
            Structured analysis
        """
        logger.info(f"Parsing Devin session result. Full session data: {session}")

        result = session.get("result", {})

        # Try to extract actual response from various possible fields
        actual_response = None

        # Check common response fields at various levels
        response_fields = ["output", "response", "message", "text", "content", "body", "data", "answer", "completion"]

        # Check top-level session fields
        for field in response_fields:
            if field in session and session[field]:
                actual_response = session[field]
                logger.info(f"Found Devin response in session.{field}")
                break

        # Check result sub-object if not found
        if not actual_response and result:
            for field in response_fields:
                if field in result and result[field]:
                    actual_response = result[field]
                    logger.info(f"Found Devin response in result.{field}")
                    break

        # Check nested data field
        if not actual_response and "data" in session and isinstance(session["data"], dict):
            for field in response_fields:
                if field in session["data"] and session["data"][field]:
                    actual_response = session["data"][field]
                    logger.info(f"Found Devin response in data.{field}")
                    break

        # Check messages array for devin_message entries
        if not actual_response and "messages" in session and isinstance(session["messages"], list):
            logger.info(f"Looking for Devin responses in messages array with {len(session['messages'])} messages")
            devin_messages = []
            for msg in session["messages"]:
                if isinstance(msg, dict):
                    message_content = None
                    
                    # Handle original Devin API format
                    if msg.get("type") == "devin_message":
                        message_content = msg.get("message", "")
                    # Handle streaming formatted messages 
                    elif msg.get("type") == "devin_response" or (msg.get("role") == "assistant" and msg.get("type") != "user_request"):
                        message_content = msg.get("content", "")
                    
                    if message_content:
                        devin_messages.append(message_content)
                        logger.info(f"Found devin message: {message_content[:100]}...")
            
            if devin_messages:
                # Combine all devin messages, with the last one typically being the most comprehensive
                actual_response = "\n\n".join(devin_messages)
                logger.info(f"Combined {len(devin_messages)} devin_message(s) into response")

        # Check messages array in raw_data (fallback for streaming data)
        if not actual_response and "raw_data" in session and "messages" in session["raw_data"]:
            raw_messages = session["raw_data"]["messages"]
            logger.info(f"Checking raw_data messages array with {len(raw_messages)} messages")
            devin_messages = []
            for msg in raw_messages:
                if isinstance(msg, dict) and msg.get("type") == "devin_message":
                    message_content = msg.get("message", "")
                    if message_content:
                        devin_messages.append(message_content)
                        logger.info(f"Found raw devin_message: {message_content[:100]}...")
            
            if devin_messages:
                actual_response = "\n\n".join(devin_messages)
                logger.info(f"Combined {len(devin_messages)} raw devin_message(s) into response")

        # Log what we found
        if actual_response:
            logger.info(f"Devin response preview: {str(actual_response)[:200]}...")
        else:
            logger.warning(f"No Devin response found. Available session keys: {list(session.keys())}")
            if result:
                logger.warning(f"Available result keys: {list(result.keys())}")

        # Extract structured data if provided in result
        summary = result.get("summary")
        confidence = result.get("confidence")
        steps = result.get("steps")

        # If we have actual response text, parse it to extract structured data
        if actual_response and isinstance(actual_response, str):
            logger.info("Parsing Devin text response to extract structured data")
            parsed_data = self._parse_devin_text_response(actual_response)

            # Use parsed data if we don't have structured data already
            if not summary and parsed_data.get("summary"):
                summary = parsed_data["summary"]
                logger.info(f"Using parsed summary from Devin response")

            if not confidence and parsed_data.get("confidence"):
                confidence = parsed_data["confidence"]
                logger.info(f"Using parsed confidence from Devin response: {confidence}")

            if (not steps or len(steps) == 0) and parsed_data.get("steps"):
                steps = parsed_data["steps"]
                logger.info(f"Using parsed steps from Devin response: {len(steps)} steps")

            # If summary is still empty after parsing, use the full response
            if not summary:
                summary = str(actual_response)
                logger.info(f"Using full Devin response as summary")

        # Fall back to default summary only if no content at all
        if not summary:
            summary = "Analysis in progress - Devin has not provided output yet"
            logger.warning(f"No summary found in Devin response")

        # Use heuristic-based confidence if Devin doesn't provide one
        if not confidence:
            confidence = self._calculate_confidence_heuristic(issue)
            logger.info(f"Using heuristic confidence: {confidence}")

        # Only use generic steps if Devin didn't provide any
        if not steps or len(steps) == 0:
            logger.warning(f"No steps found in Devin response - using generic fallback")
            steps = [
                "Review the issue requirements",
                "Identify affected files",
                "Implement the necessary changes",
                "Add tests for the changes",
                "Update documentation if needed"
            ]
        else:
            logger.info(f"Using Devin-provided steps: {steps}")

        parsed_result = {
            "session_id": session_id,
            "summary": summary,
            "confidence": confidence,
            "steps": steps,
            "status": session.get("status", "completed")
        }

        # Include raw response if available for debugging
        if actual_response:
            parsed_result["devin_raw_response"] = str(actual_response)[:1000]  # Truncate for logging

        # Log the final parsed result (without full raw response to keep logs clean)
        logger.info(f"Successfully parsed Devin analysis:")
        logger.info(f"  - Status: {parsed_result['status']}")
        logger.info(f"  - Summary length: {len(summary) if summary else 0} chars")
        logger.info(f"  - Confidence: {confidence}")
        logger.info(f"  - Steps count: {len(steps) if steps else 0}")
        logger.info(f"  - Has raw response: {bool(actual_response)}")

        return parsed_result
    
    def _create_fallback_analysis(self, issue: Dict[str, Any], error: str) -> Dict[str, Any]:
        """
        Create a fallback analysis when Devin API is unavailable

        Args:
            issue: GitHub issue
            error: Error message

        Returns:
            Fallback analysis
        """
        logger.warning(f"Using fallback analysis due to error: {error}")

        # Simple heuristic-based analysis
        labels = [label["name"].lower() for label in issue.get("labels", [])]

        # Determine confidence based on issue characteristics
        confidence = self._calculate_confidence_heuristic(issue)

        summary = f"This appears to be a {labels[0] if labels else 'general'} issue that requires investigation and implementation."

        steps = [
            "Analyze the issue requirements in detail",
            "Locate the relevant code sections",
            "Implement the proposed solution",
            "Write or update tests",
            "Review and validate the changes"
        ]

        # Customize note based on error type
        if "rate limit" in error.lower() or "429" in error:
            note = "Devin API rate limit reached. This is a fallback analysis. Please try again in a few minutes for AI-powered analysis."
        else:
            note = "This is a fallback analysis. Devin API integration may need configuration."

        return {
            "session_id": "fallback-session",
            "summary": summary,
            "confidence": confidence,
            "steps": steps,
            "status": "completed",
            "note": note
        }

    def _create_fallback_execution(self, issue: Dict[str, Any], analysis: Dict[str, Any], error: str) -> Dict[str, Any]:
        """
        Create a fallback execution result when Devin API is unavailable

        Args:
            issue: GitHub issue
            analysis: Analysis results
            error: Error message

        Returns:
            Fallback execution result
        """
        logger.warning(f"Using fallback execution due to error: {error}")

        issue_number = issue.get("number", "unknown")
        issue_title = issue.get("title", "Unknown Issue")

        # Provide helpful message about manual execution
        message = "Devin API is currently unavailable. "
        if "rate limit" in error.lower() or "429" in error:
            message += "You've hit the API rate limit. Please try again in a few minutes, or implement the solution manually using the analysis above."
        else:
            message += "Please implement the solution manually using the analysis above, or try again later."

        return {
            "session_id": "fallback-execution",
            "status": "unavailable",
            "message": message,
            "issue_number": issue_number,
            "issue_title": issue_title,
            "manual_steps": analysis.get("steps", []),
            "note": f"Devin API Error: {error}. Manual implementation required."
        }

devin_service = DevinService()

