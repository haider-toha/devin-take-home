import requests
from typing import List, Dict, Any, Optional
import logging
from config import settings

logger = logging.getLogger(__name__)

class GitHubService:
    """Service for interacting with GitHub API"""
    
    def __init__(self):
        self.base_url = settings.github_api_base
        self.repo = settings.github_repo
        self.headers = settings.github_headers
    
    def get_issues(self, state: str = "open", per_page: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch issues from the GitHub repository
        
        Args:
            state: Issue state (open, closed, all)
            per_page: Number of issues per page
            
        Returns:
            List of issue dictionaries
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}/issues"
            params = {
                "state": state,
                "per_page": per_page,
                "sort": "created",
                "direction": "desc"
            }
            
            logger.info(f"Fetching issues from {self.repo}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            issues = response.json()
            # Filter out pull requests (they show up in issues endpoint)
            issues = [issue for issue in issues if "pull_request" not in issue]
            
            logger.info(f"Successfully fetched {len(issues)} issues")
            return issues
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issues: {str(e)}")
            raise Exception(f"Failed to fetch issues from GitHub: {str(e)}")
    
    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Fetch a specific issue by number
        
        Args:
            issue_number: The issue number
            
        Returns:
            Issue dictionary
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}"
            
            logger.info(f"Fetching issue #{issue_number} from {self.repo}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            issue = response.json()
            logger.info(f"Successfully fetched issue #{issue_number}")
            return issue
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issue #{issue_number}: {str(e)}")
            raise Exception(f"Failed to fetch issue #{issue_number}: {str(e)}")
    
    def post_comment(self, issue_number: int, comment: str) -> Dict[str, Any]:
        """
        Post a comment on a GitHub issue
        
        Args:
            issue_number: The issue number
            comment: Comment text
            
        Returns:
            Comment response
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/comments"
            payload = {"body": comment}
            
            logger.info(f"Posting comment to issue #{issue_number}")
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully posted comment to issue #{issue_number}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting comment to issue #{issue_number}: {str(e)}")
            raise Exception(f"Failed to post comment: {str(e)}")
    
    def format_analysis_comment(self, analysis: Dict[str, Any]) -> str:
        """
        Format analysis results as a GitHub comment
        
        Args:
            analysis: Analysis results from Devin
            
        Returns:
            Formatted markdown comment
        """
        confidence_pct = int(analysis.get("confidence", 0) * 100)
        summary = analysis.get("summary", "No summary available")
        steps = analysis.get("steps", [])
        
        comment = f"""**Devin AI Analysis**

**Summary:** {summary}

**Confidence Score:** {confidence_pct}%

**Proposed Implementation Steps:**
"""
        
        for i, step in enumerate(steps, 1):
            comment += f"\n{i}. {step}"
        
        comment += "\n\n---\n*This analysis was generated automatically by Devin AI*"
        
        return comment

github_service = GitHubService()

