import os
from typing import Optional

class Settings:
    """Application settings"""
    
    def __init__(self):
        self.github_token: Optional[str] = os.getenv("GITHUB_TOKEN")
        self.github_repo: Optional[str] = os.getenv("GITHUB_REPO")
        self.devin_api_key: Optional[str] = os.getenv("DEVIN_API_KEY")
        self.frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
        
        # API URLs
        self.github_api_base = "https://api.github.com"
        self.devin_api_base = "https://api.devin.ai/v1"
    
    def validate(self) -> bool:
        """Validate that all required settings are present"""
        return all([
            self.github_token,
            self.github_repo,
            self.devin_api_key
        ])
    
    @property
    def github_headers(self) -> dict:
        """Get GitHub API headers"""
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    @property
    def devin_headers(self) -> dict:
        """Get Devin API headers"""
        return {
            "Authorization": f"Bearer {self.devin_api_key}",
            "Content-Type": "application/json"
        }

settings = Settings()

