import requests
from typing import Dict, Any, Optional, List
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
            
            # Construct analysis prompt with specific structure request
            prompt = f"""Analyze this GitHub issue and provide your response in the following EXACT JSON format:

{{
  "summary": "A comprehensive summary of what needs to be done (2-4 sentences)",
  "detailed_analysis": "A detailed technical analysis explaining the approach, challenges, and solution overview (5-8 sentences)",
  "confidence": 0.85,
  "confidence_reasoning": "Brief explanation of why you have this confidence level",
  "implementation_steps": [
    "Step 1: Clear, actionable step",
    "Step 2: Another clear step",
    "Step 3: Continue with logical progression"
  ],
  "complexity": "Low/Medium/High",
  "potential_challenges": ["Challenge 1", "Challenge 2"],
  "success_criteria": ["Criteria 1", "Criteria 2"]
}}

GitHub Issue #{issue_number}:
Title: {issue_title}

Description:
{issue_body or 'No description provided'}

Labels: {', '.join(issue_labels) if issue_labels else 'None'}

IMPORTANT: Respond ONLY with the JSON object above, no additional text or formatting. The JSON must be valid and parseable."""

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
                        # Enhanced categorization for better streaming experience
                        content_lower = msg_content.lower()
                        
                        # Check if this looks like a thinking/progress step
                        if (len(msg_content) < 300 and 
                            any(keyword in content_lower for keyword in 
                                ["analyzing", "examining", "looking", "checking", "investigating", 
                                 "let me", "i'll", "starting", "first", "next", "now"])):
                            # Short messages with analysis keywords are thinking steps
                            thinking_steps.append({
                                "content": msg_content,
                                "timestamp": msg_timestamp
                            })
                        # Check if it's a structured analysis response  
                        elif ("summary" in content_lower and "confidence" in content_lower and 
                              ("step" in content_lower or "plan" in content_lower)):
                            # This is likely the main structured analysis - split into parts for streaming
                            sections = msg_content.split('\n\n')
                            for i, section in enumerate(sections):
                                if section.strip():
                                    if i == 0 or len(section) < 200:
                                        # First section or short sections as thinking steps
                                        thinking_steps.append({
                                            "content": section.strip(),
                                            "timestamp": msg_timestamp
                                        })
                                    else:
                                        # Longer sections as messages
                                        formatted_messages.append({
                                            "content": section.strip(),
                                            "role": "assistant",
                                            "timestamp": msg_timestamp,
                                            "type": "devin_analysis_section"
                                        })
                        else:
                            # Regular messages
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
            
            # If we still don't have thinking steps, create them from message sections
            if not thinking_steps and formatted_messages:
                # Look for structured content in the messages and break it down
                for msg in formatted_messages[:]:  # Copy list to modify during iteration
                    content = msg["content"]
                    
                    # If this is a long structured message, break it into thinking steps
                    if len(content) > 500 and any(marker in content for marker in ["###", "**", "Phase", "Step"]):
                        # Remove from messages and break into thinking steps
                        formatted_messages.remove(msg)
                        
                        # Split on section markers
                        sections = []
                        for delimiter in ['\n###', '\n**', '\nPhase', '\nStep']:
                            if delimiter in content:
                                sections = content.split(delimiter)
                                break
                        
                        if not sections:
                            sections = [content]
                        
                        # Add sections as thinking steps (except the first if it's just a title)
                        for i, section in enumerate(sections):
                            if section.strip():
                                clean_section = section.strip()
                                if len(clean_section) > 20:  # Skip very short sections
                                    thinking_steps.append({
                                        "content": clean_section,
                                        "timestamp": msg["timestamp"]
                                    })
                
                # If we still don't have thinking steps, create one from the analysis flow
                if not thinking_steps and formatted_messages:
                    thinking_steps.append({
                        "content": "Analyzing GitHub issue and generating comprehensive implementation plan...",
                        "timestamp": formatted_messages[0]["timestamp"] if formatted_messages else ""
                    })
            
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

        # Extract summary section - look for comprehensive summary
        # Pattern 1: Look for "## 1. Summary" or "### 1. Summary" with detailed content
        summary_match = re.search(r'(?:^|\n)#+\s*(?:\d+\.\s*)?summary[:\s]*\n(.*?)(?=\n#+|\n## \d+\.|\n### \d+\.)', text, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(1).strip()
            # Take the full summary content, not just first paragraph
            parsed["summary"] = summary_text[:800].strip()  # Increased limit for detailed summaries
            logger.info(f"Extracted detailed summary: {parsed['summary'][:100]}...")
        else:
            # Pattern 2: Look for "Summary:" followed by content
            simple_summary_match = re.search(r'(?:^|\n)(?:\d+\.\s*)?summary[:\s]*\n(.+?)(?=\n\d+\.|$)', text, re.IGNORECASE | re.DOTALL)
            if simple_summary_match:
                summary_text = simple_summary_match.group(1).strip()
                # Take first meaningful section 
                sections = summary_text.split('\n\n')
                if len(sections) > 1:
                    # Combine first few sections for comprehensive summary
                    combined_summary = '\n\n'.join(sections[:3])  # Take first 3 sections
                    parsed["summary"] = combined_summary[:800].strip()
                else:
                    parsed["summary"] = summary_text[:500].strip()
                logger.info(f"Extracted simple summary: {parsed['summary'][:100]}...")
            else:
                # Fallback: Look for any meaningful content after analysis title
                lines = text.strip().split('\n')
                if len(lines) > 2:
                    # Find the first substantial paragraph
                    for i, line in enumerate(lines[1:], 1):  # Skip first line
                        if line.strip() and not re.match(r'^\d+\.', line.strip()) and len(line.strip()) > 50:
                            # Check if this looks like analysis content
                            if any(keyword in line.lower() for keyword in ['framework', 'api', 'documentation', 'endpoints', 'task involves']):
                                parsed["summary"] = line.strip()
                                logger.info(f"Using content-based summary: {parsed['summary'][:100]}...")
                                break
                    if not parsed["summary"] and len(text) > 100:
                        parsed["summary"] = text[:500].strip()

        # Extract steps from various formats - prioritize main phases over detailed sub-steps
        # Pattern 1: Direct "Phase N: Title" matches - highest priority for implementation phases
        phase_matches = re.findall(r'(?:^|\n)#{1,4}\s*Phase\s+\d+:\s*([^\n]+)', text, re.IGNORECASE | re.MULTILINE)
        if phase_matches and len(phase_matches) >= 3:
            parsed["steps"] = phase_matches
            logger.info(f"Extracted {len(parsed['steps'])} main phases from headers")
        else:
            # Pattern 2: Look for phases in bullet points or numbered lists
            phase_in_text = re.findall(r'(?:^|\n)[*\-]?\s*(?:\d+\.\s*)?(?:Phase\s+\d+:\s*)?([^(\n]*\([Dd]ays?\s+\d+[^\)]*\))', text, re.MULTILINE)
            if phase_in_text and len(phase_in_text) >= 3:
                # Clean up the phase descriptions
                cleaned_phases = []
                for phase in phase_in_text:
                    clean_phase = re.sub(r'^\**\s*', '', phase.strip())  # Remove leading asterisks
                    if len(clean_phase) > 10 and 'day' in clean_phase.lower():  # Ensure it's a meaningful phase with duration
                        cleaned_phases.append(clean_phase)
                
                if len(cleaned_phases) >= 3:
                    parsed["steps"] = cleaned_phases
                    logger.info(f"Extracted {len(parsed['steps'])} implementation phases with durations")
            
            # Pattern 3: Look for main section headers as phases (avoid detailed sub-steps)
            if not parsed["steps"]:
                section_headers = re.findall(r'(?:^|\n)###?\s+([^:\n]*(?:Generation|Documentation|Guides|SDK|Infrastructure)[^\n]*)', text, re.IGNORECASE | re.MULTILINE)
                if section_headers and len(section_headers) >= 3:
                    parsed["steps"] = section_headers
                    logger.info(f"Extracted {len(parsed['steps'])} main sections as phases")
            
            # Pattern 4: Generic numbered patterns (heavily filtered to avoid sub-steps)
            if not parsed["steps"]:
                step_patterns = [
                    r'(?:^|\n)(\d+)\.\s*([^\n]+)',  # "1. Step"
                ]

                for pattern in step_patterns:
                    matches = re.findall(pattern, text, re.MULTILINE)
                    if matches and len(matches) >= 3:
                        # Heavy filtering - only keep high-level implementation steps
                        filtered_matches = []
                        for match in matches:
                            match_text = match[1] if len(match) > 1 else match[0]
                            # Only include if it looks like a main phase, not a detailed sub-step
                            if (any(keyword in match_text.lower() for keyword in ['specification', 'documentation', 'guides', 'sdk', 'infrastructure', 'openapi', 'interactive']) and
                                not any(skip_keyword in match_text.lower() for skip_keyword in ['step 1.', 'step 2.', 'add swagger', 'define schemas', 'tutorial 1', 'example 1', 'documented in openapi', 'accessible and functional'])):
                                filtered_matches.append(match)
                        
                        # Only use if we get a reasonable number of main phases (3-10)
                        if 3 <= len(filtered_matches) <= 10:
                            parsed["steps"] = [match[1] if len(match) > 1 else match[0] for match in filtered_matches]
                            logger.info(f"Extracted {len(parsed['steps'])} main phases using heavily filtered pattern")
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
        import json
        logger.info(f"Parsing Devin session result. Full session data keys: {list(session.keys())}")

        # Extract the actual response from Devin
        actual_response = self._extract_devin_response(session)
        
        if actual_response:
            logger.info(f"Devin response preview: {str(actual_response)[:200]}...")
            
            # First, try to parse as JSON (new structured format)
            try:
                # Clean the response - sometimes Devin adds markdown formatting
                cleaned_response = actual_response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]  # Remove ```
                cleaned_response = cleaned_response.strip()
                
                parsed_json = json.loads(cleaned_response)
                logger.info("Successfully parsed Devin response as JSON")
                
                # Ensure steps is always a list, never None
                steps = parsed_json.get("implementation_steps", [])
                if not isinstance(steps, list):
                    steps = self._get_fallback_steps()
                
                return {
                    "session_id": session_id,
                    "summary": parsed_json.get("summary", ""),
                    "detailed_analysis": parsed_json.get("detailed_analysis", ""),
                    "confidence": parsed_json.get("confidence", self._calculate_confidence_heuristic(issue)),
                    "confidence_reasoning": parsed_json.get("confidence_reasoning", ""),
                    "steps": steps,
                    "complexity": parsed_json.get("complexity", "Medium"),
                    "potential_challenges": parsed_json.get("potential_challenges", []),
                    "success_criteria": parsed_json.get("success_criteria", []),
                    "status": session.get("status", "completed")
                }
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse Devin response as JSON: {str(e)}")
                logger.info("Falling back to text parsing")
                
                # Fallback: Parse as text using the old method
                parsed_data = self._parse_devin_text_response(actual_response)
                
                # Ensure steps is always a list, never None
                steps = parsed_data.get("steps")
                if not isinstance(steps, list):
                    steps = self._get_fallback_steps()
                
                return {
                    "session_id": session_id,
                    "summary": parsed_data.get("summary", actual_response[:500]),
                    "detailed_analysis": "",
                    "confidence": parsed_data.get("confidence", self._calculate_confidence_heuristic(issue)),
                    "confidence_reasoning": "",
                    "steps": steps,
                    "complexity": "Medium",
                    "potential_challenges": [],
                    "success_criteria": [],
                    "status": session.get("status", "completed")
                }
        else:
            # No response found - return fallback
            logger.warning("No Devin response found, using fallback analysis")
            fallback_steps = self._get_fallback_steps()
            
            return {
                "session_id": session_id,
                "summary": "Analysis in progress - Devin has not provided output yet",
                "detailed_analysis": "",
                "confidence": self._calculate_confidence_heuristic(issue),
                "confidence_reasoning": "Based on issue characteristics and labels",
                "steps": fallback_steps if isinstance(fallback_steps, list) else [],
                "complexity": "Medium",
                "potential_challenges": [],
                "success_criteria": [],
                "status": session.get("status", "running")
            }

    def _extract_devin_response(self, session: Dict[str, Any]) -> str:
        """Extract Devin's response from various possible locations in the session data"""
        
        # Check common response fields at various levels
        response_fields = ["output", "response", "message", "text", "content", "body", "data", "answer", "completion"]

        # Check top-level session fields
        for field in response_fields:
            if field in session and session[field]:
                logger.info(f"Found Devin response in session.{field}")
                return str(session[field])

        # Check result sub-object if present
        result = session.get("result", {})
        if result:
            for field in response_fields:
                if field in result and result[field]:
                    logger.info(f"Found Devin response in result.{field}")
                    return str(result[field])

        # Check messages array for devin_message entries
        if "messages" in session and isinstance(session["messages"], list):
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
                # Use the last message which is typically the most complete
                return devin_messages[-1]

        # Check raw_data messages array (fallback)
        if "raw_data" in session and "messages" in session["raw_data"]:
            raw_messages = session["raw_data"]["messages"]
            logger.info(f"Checking raw_data messages array with {len(raw_messages)} messages")
            for msg in raw_messages:
                if isinstance(msg, dict) and msg.get("type") == "devin_message":
                    message_content = msg.get("message", "")
                    if message_content:
                        logger.info(f"Found raw devin_message: {message_content[:100]}...")
                        return message_content

        logger.warning(f"No Devin response found. Available session keys: {list(session.keys())}")
        return None

    def _get_fallback_steps(self) -> List[str]:
        """Get generic fallback steps when Devin doesn't provide specific ones"""
        return [
            "Review the issue requirements in detail",
            "Identify affected files and components",
            "Implement the necessary changes",
            "Add tests for the changes",
            "Update documentation if needed"
        ]
    
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

