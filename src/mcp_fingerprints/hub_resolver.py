"""
Hub Link & Missing Repository URL Resolution for PyPI and npm Passports.
"""
import json
import ssl
import urllib.request
import urllib.error
import socket

def normalize_github_url(url: str) -> str:
    """Clean and normalize a GitHub repository URL."""
    if not url:
        return ""
    
    url = url.strip()
    
    # Handle git+ prefixes
    if url.startswith("git+"):
        url = url[4:]
    if url.startswith("git://"):
        url = "https://" + url[6:]
    if url.startswith("ssh://git@"):
        url = "https://" + url[10:]
    
    # Handle ssh format like git@github.com:user/repo.git
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url[15:]
        
    # Remove .git suffix
    if url.endswith(".git"):
        url = url[:-4]
        
    # Normalize github.com links
    if "github.com" in url:
        # Some URLs might have trailing slashes
        url = url.rstrip("/")
        
    return url

def _fetch_json(url: str, timeout: int = 5) -> dict:
    """Fetch JSON from a URL with graceful fallback for SSL errors."""
    req = urllib.request.Request(url, headers={"User-Agent": "MCP-Fingerprints-Hub-Resolver/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLError):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
                return json.loads(response.read().decode())
        raise e

def resolve_pypi_repository(package_name: str) -> str | None:
    """Query PyPI for package metadata to find the GitHub URL."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        data = _fetch_json(url)
        project_urls = data.get("info", {}).get("project_urls", {}) or {}
        
        # Check specific keys in order of preference
        for key in ["Source", "Repository", "Code", "Homepage"]:
            if key in project_urls and project_urls[key]:
                val = project_urls[key]
                if "github.com" in val:
                    return normalize_github_url(val)
                    
        # Fallback to homepage if not in project_urls but exists in info
        homepage = data.get("info", {}).get("home_page")
        if homepage and "github.com" in homepage:
            return normalize_github_url(homepage)
            
    except (urllib.error.URLError, json.JSONDecodeError, socket.timeout):
        pass
        
    return None

def resolve_npm_repository(package_name: str) -> str | None:
    """Query npm registry for package metadata to find the GitHub URL."""
    url = f"https://registry.npmjs.org/{package_name}"
    try:
        data = _fetch_json(url)
        
        # Check repository field
        repo = data.get("repository")
        if isinstance(repo, dict):
            repo_url = repo.get("url")
            if repo_url and "github.com" in repo_url:
                return normalize_github_url(repo_url)
        elif isinstance(repo, str):
            if "github.com" in repo:
                return normalize_github_url(repo)
                
        # Fallback to homepage
        homepage = data.get("homepage")
        if homepage and isinstance(homepage, str) and "github.com" in homepage:
            return normalize_github_url(homepage)
            
    except (urllib.error.URLError, json.JSONDecodeError, socket.timeout):
        pass
        
    return None
