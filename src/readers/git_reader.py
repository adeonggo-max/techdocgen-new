"""Git repository reader"""

import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
try:
    import git
except ImportError:
    git = None
from .base_reader import BaseReader


class GitReader(BaseReader):
    """Reads source code from a Git repository"""
    
    def __init__(self, repo_path: str, branch: Optional[str] = None, config: Dict[str, Any] = None):
        super().__init__(config)
        self.repo_path = Path(repo_path)
        self.branch = branch
        self.repo = None
    
    def _normalize_url(self, url: str) -> str:
        """Normalize and fix common URL issues"""
        # Fix missing slash in protocol (e.g., https:/ -> https://)
        url = re.sub(r'^(https?):/([^/])', r'\1://\2', url)
        url = re.sub(r'^(http?):/([^/])', r'\1://\2', url)
        
        # Ensure URLs ending with .git are preserved
        if url.startswith('http') and not url.endswith('.git') and '/' in url:
            # Check if it looks like a GitHub/GitLab URL that should end with .git
            if 'github.com' in url or 'gitlab.com' in url:
                if not url.endswith('.git') and not url.endswith('/'):
                    url = url.rstrip('/') + '.git'
        
        return url
    
    def _get_clone_path(self, repo_url: str) -> Path:
        """Get the clone path for a repository URL"""
        # Extract repo name from URL
        repo_name = Path(repo_url).stem
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        if not repo_name:
            # Fallback: use last part of URL path
            repo_name = Path(repo_url.rstrip('/').rstrip('.git')).name or "repo"
        return Path("./temp_repos") / repo_name
    
    def _cleanup_existing_clone(self, clone_path: Path):
        """Remove existing clone directory if it exists"""
        if clone_path.exists():
            try:
                # Check if it's a valid git repo
                test_repo = git.Repo(clone_path)
                # If it's valid, we can reuse it, so don't remove
                return False
            except:
                # Not a valid git repo or doesn't exist, remove it
                if clone_path.is_dir():
                    shutil.rmtree(clone_path)
                elif clone_path.exists():
                    clone_path.unlink()
                return True
        return False
    
    def _clone_or_open(self):
        """Clone repository if URL, or open if local path"""
        if git is None:
            raise ImportError("GitPython is required for Git repository support. Install it with: pip install GitPython")
        
        if not self.repo_path.exists():
            # Assume it's a URL
            repo_url = str(self.repo_path)
            
            # Normalize URL to fix common issues
            repo_url = self._normalize_url(repo_url)
            
            # Get clone path
            clone_path = self._get_clone_path(repo_url)
            clone_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if clone path already exists and handle it
            if clone_path.exists():
                try:
                    # Try to open existing repo
                    existing_repo = git.Repo(clone_path)
                    print(f"Using existing repository at {clone_path}")
                    self.repo = existing_repo
                    self.repo_path = clone_path
                    # Pull latest changes
                    try:
                        self.repo.remotes.origin.pull()
                        print(f"Updated repository with latest changes")
                    except:
                        print(f"Warning: Could not update repository, using existing version")
                except:
                    # Existing path is not a valid git repo, remove it
                    print(f"Removing invalid existing directory at {clone_path}")
                    self._cleanup_existing_clone(clone_path)
            
            # Clone if we don't have a repo yet
            if self.repo is None:
                # Convert SSH URLs to HTTPS for public repos to avoid SSH config issues
                if repo_url.startswith('git@') or (repo_url.startswith('ssh://')):
                    # Try SSH first, but have HTTPS as fallback
                    try:
                        print(f"Cloning repository from {repo_url}...")
                        self.repo = git.Repo.clone_from(repo_url, str(clone_path))
                        self.repo_path = clone_path
                    except Exception as ssh_error:
                        # Try converting to HTTPS
                        if 'github.com' in repo_url or 'github.ibm.com' in repo_url:
                            https_url = repo_url.replace('git@', 'https://').replace('ssh://git@', 'https://').replace(':', '/')
                            if not https_url.startswith('http'):
                                # Handle git@github.com:user/repo.git format
                                https_url = repo_url.replace('git@', 'https://').replace(':', '/', 1)
                            print(f"SSH clone failed, trying HTTPS: {https_url}")
                            try:
                                # Clean up clone path before retry
                                self._cleanup_existing_clone(clone_path)
                                self.repo = git.Repo.clone_from(https_url, str(clone_path))
                                self.repo_path = clone_path
                            except Exception as https_error:
                                raise ValueError(
                                    f"Failed to clone repository. SSH error: {ssh_error}. "
                                    f"HTTPS error: {https_error}. "
                                    f"Please check your SSH config or use HTTPS URL."
                                )
                        else:
                            raise ValueError(f"Failed to clone repository via SSH: {ssh_error}. "
                                           f"Please check your SSH configuration or use HTTPS URL.")
                else:
                    # HTTPS or other protocol
                    print(f"Cloning repository from {repo_url}...")
                    self.repo = git.Repo.clone_from(repo_url, str(clone_path))
                    self.repo_path = clone_path
        else:
            self.repo = git.Repo(self.repo_path)
        
        # Checkout specific branch if provided
        if self.branch:
            try:
                self.repo.git.checkout(self.branch)
            except:
                print(f"Warning: Could not checkout branch {self.branch}, using current branch")
        
        return self.repo
    
    def read(self) -> List[Dict[str, Any]]:
        """Read all source code files from the Git repository"""
        try:
            self._clone_or_open()
        except Exception as e:
            raise ValueError(f"Failed to access Git repository: {e}")
        
        files = []
        extensions = self.config.get("extensions", {})
        all_extensions = []
        for exts in extensions.values():
            all_extensions.extend(exts)
        
        # Get repository root
        repo_root = Path(self.repo.working_dir)
        
        # First, collect all matching files
        matching_files = []
        print("Scanning repository for source files...")
        for file_path in repo_root.rglob("*"):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in all_extensions:
                continue
            
            if self._should_exclude(file_path):
                continue
            
            if not self._is_valid_size(file_path):
                print(f"Warning: File {file_path} exceeds size limit, skipping")
                continue
            
            matching_files.append(file_path)
        
        print(f"Found {len(matching_files)} source file(s). Reading content...")
        
        # Read file contents
        for idx, file_path in enumerate(matching_files, 1):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                language = self._detect_language(file_path)
                
                files.append({
                    "path": str(file_path),
                    "content": content,
                    "language": language,
                    "name": file_path.name,
                    "relative_path": str(file_path.relative_to(repo_root))
                })
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue
        
        print(f"Successfully read {len(files)} file(s)")
        return files

