import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import git
from github import Github
import google.generativeai as genai

from .config import Config

logger = logging.getLogger(__name__)

class GitHubProjectEvaluator:
    """Evaluates GitHub projects by cloning repos, analyzing commits, and using AI"""
    
    def __init__(self):
        
        self.github_token = Config.GITHUB_TOKEN
        self.clone_dir = Config.CLONE_DIR
        self.github = Github(self.github_token) if self.github_token else None
        
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        Path(self.clone_dir).mkdir(parents=True, exist_ok=True)
        logger.info("Evaluator ready")
    
    def parse_github_url(self, repo_url: str) -> Tuple[str, str]:
        """Extract owner and repo name from GitHub URL"""
        repo_url = repo_url.strip().rstrip('/').removesuffix('.git')
        
        if 'github.com' in repo_url:
            parts = repo_url.split('github.com/')[-1].split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]
        
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    
    def clone_repo(self, repo_url: str, team_name: str) -> str:
        """Clone repository to local directory"""
        local_path = os.path.join(self.clone_dir, team_name.replace(' ', '_'))
        
        if os.path.exists(local_path):
            logger.info(f"Removing existing clone: {local_path}")
            shutil.rmtree(local_path)
        
        try:
            logger.info(f"Cloning {repo_url} to {local_path}")
            git.Repo.clone_from(repo_url, local_path, depth=1)
            logger.info(f"Successfully cloned to {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Clone failed: {e}")
            raise
    
    def analyze_contributors(self, repo_url: str) -> Dict:
        """Get commit statistics for each contributor"""
        if not self.github:
            logger.warning("GitHub token missing, skipping contributor analysis")
            return {}
        
        try:
            owner, repo_name = self.parse_github_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            contributors_data = {}
            
            # Get contributors
            for contributor in repo.get_contributors():
                logger.info(f"Analyzing contributor: {contributor.login}")
                
                # Get commits by this contributor
                commits = list(repo.get_commits(author=contributor)[:50])  # Limit to 50 recent commits
                
                total_additions = 0
                total_deletions = 0
                commit_messages = []
                files_modified = set()
                
                for commit in commits:
                    try:
                        files = commit.files
                        for f in files:
                            total_additions += f.additions
                            total_deletions += f.deletions
                            files_modified.add(f.filename)
                        
                        commit_messages.append(commit.commit.message.split('\n')[0])  # First line only
                    except Exception as e:
                        logger.warning(f"Error processing commit {commit.sha}: {e}")
                        continue
                
                contributors_data[contributor.login] = {
                    "name": contributor.name or contributor.login,
                    "commits": len(commits),
                    "additions": total_additions,
                    "deletions": total_deletions,
                    "net_lines": total_additions - total_deletions,
                    "files_modified": len(files_modified),
                    "sample_commits": commit_messages[:5],  # Sample of 5 commit messages
                    "contribution_percentage": 0  # Will be calculated after all contributors
                }
            
            total_commits = sum(c["commits"] for c in contributors_data.values())
            if total_commits > 0:
                for data in contributors_data.values():
                    data["contribution_percentage"] = round((data["commits"] / total_commits) * 100, 2)
            
            logger.info(f"Analyzed {len(contributors_data)} contributors")
            return contributors_data
            
        except Exception as e:
            logger.error(f"Contributor analysis error: {e}")
            return {}
    
    def extract_code_files(self, local_path: str, max_files: int = 50) -> Dict[str, str]:
        """Extract code files from the repository"""
        code_files = {}
        
        extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.cs',
            '.html', '.css', '.scss', '.json', '.xml', '.yaml', '.yml',
            '.md', '.sql', '.sh', '.php', '.rb', '.go', '.rs', '.swift'
        }
        
        skip_dirs = {
            'node_modules', '.git', 'venv', '.venv', 'env', '__pycache__',
            'dist', 'build', '.next', 'out', 'target', 'bin', 'obj', '.pytest_cache'
        }
        
        important_files = {
            'README.md', 'package.json', 'requirements.txt', 'Dockerfile',
            'docker-compose.yml', '.gitignore', 'tsconfig.json', 'webpack.config.js'
        }
        
        file_count = 0
        
        for root, dirs, files in os.walk(local_path):
            # Remove skip directories from traversal
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if file_count >= max_files:
                    break
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, local_path)
                
                # Include important files or files with target extensions
                if file in important_files or any(file.endswith(ext) for ext in extensions):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # Skip very large files (>100KB)
                            if len(content) < 100000:
                                code_files[relative_path] = content
                                file_count += 1
                    except Exception as e:
                        logger.warning(f"Could not read {relative_path}: {e}")
            
            if file_count >= max_files:
                break
        
        logger.info(f"Extracted {len(code_files)} code files")
        return code_files
    
    def generate_repo_structure(self, local_path: str) -> str:
        """Generate a tree structure of the repository"""
        skip_dirs = {'node_modules', '.git', 'venv', '.venv', 'env', '__pycache__', 'dist', 'build'}
        
        structure = []
        
        for root, dirs, files in os.walk(local_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            level = root.replace(local_path, '').count(os.sep)
            indent = '  ' * level
            folder_name = os.path.basename(root)
            
            if level == 0:
                structure.append(f"{folder_name}/")
            else:
                structure.append(f"{indent}{folder_name}/")
            
            sub_indent = '  ' * (level + 1)
            for file in sorted(files)[:10]:  # Limit files per directory
                structure.append(f"{sub_indent}{file}")
        
        return '\n'.join(structure[:100])  # Limit total lines
    
    def evaluate_project(
        self, 
        local_path: str, 
        contributors_data: Dict,
        rubric: Optional[Dict] = None
    ) -> Dict:
        """Evaluate project using Gemini AI"""
        
        # Extract code and structure
        code_files = self.extract_code_files(local_path)
        repo_structure = self.generate_repo_structure(local_path)
        
        # Prepare code samples (limit size for API)
        code_samples = []
        total_chars = 0
        max_chars = 50000  # Limit for API
        
        # Prioritize important files
        priority_files = ['README.md', 'package.json', 'requirements.txt']
        for filename in priority_files:
            for path, content in code_files.items():
                if filename in path:
                    code_samples.append(f"=== {path} ===\n{content[:2000]}\n")
                    total_chars += len(content[:2000])
        
        # Add other files
        for path, content in code_files.items():
            if total_chars >= max_chars:
                break
            if not any(pf in path for pf in priority_files):
                snippet = content[:1000]
                code_samples.append(f"=== {path} ===\n{snippet}\n")
                total_chars += len(snippet)
        
        code_content = '\n'.join(code_samples)
        
        # Format contributor information
        contributor_summary = self._format_contributors(contributors_data)
        
        # Build evaluation prompt
        prompt = f"""You are an expert code reviewer evaluating a fullstack web development project.

PROJECT STRUCTURE:
{repo_structure}

CONTRIBUTORS ANALYSIS:
{contributor_summary}

CODE SAMPLES:
{code_content}

EVALUATION CRITERIA:
1. Frontend (25 points):
   - UI/UX design quality
   - Component architecture and reusability
   - State management approach
   - Responsive design implementation
   - Code organization

2. Backend (25 points):
   - API design and RESTful principles
   - Database schema design
   - Error handling and validation
   - Security practices (authentication, authorization)
   - Code structure and modularity

3. Code Quality (20 points):
   - Code readability and maintainability
   - Documentation (comments, README)
   - Testing coverage
   - Code organization and best practices
   - Dependency management

4. Git Practices (15 points):
   - Commit message quality
   - Commit frequency and consistency
   - Branch strategy (if applicable)
   - Code review and collaboration

5. Individual Contributions (15 points):
   - Balanced workload distribution
   - Quality of individual contributions
   - Collaboration and teamwork

Provide your evaluation in JSON format:
{{
  "total_score": <0-100>,
  "breakdown": {{
    "frontend": <0-25>,
    "backend": <0-25>,
    "code_quality": <0-20>,
    "git_practices": <0-15>,
    "individual_contributions": <0-15>
  }},
  "individual_scores": {{
    "username1": <0-100>,
    "username2": <0-100>
  }},
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"],
  "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
  "detailed_feedback": "Comprehensive feedback paragraph about the project"
}}

Be fair, constructive, and specific in your evaluation."""
        
        try:
            logger.info("Sending evaluation request to Gemini API")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            logger.info("Successfully evaluated project")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response.text}")
            # Return a default structure
            return self._get_default_evaluation()
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            return self._get_default_evaluation()
    
    def _format_contributors(self, contributors_data: Dict) -> str:
        """Format contributor data for display"""
        if not contributors_data:
            return "No contributor data available."
        
        lines = []
        for username, data in contributors_data.items():
            lines.append(f"- {data.get('name', username)}:")
            lines.append(f"  - Commits: {data.get('commits', 0)}")
            lines.append(f"  - Lines added: +{data.get('additions', 0)}")
            lines.append(f"  - Lines deleted: -{data.get('deletions', 0)}")
            lines.append(f"  - Net contribution: {data.get('net_lines', 0)} lines")
            lines.append(f"  - Contribution %: {data.get('contribution_percentage', 0)}%")
            lines.append(f"  - Files modified: {data.get('files_modified', 0)}")
            
            sample_commits = data.get('sample_commits', [])
            if sample_commits:
                lines.append(f"  - Sample commits:")
                for commit in sample_commits[:3]:
                    lines.append(f"    * {commit}")
        
        return '\n'.join(lines)
    
    def _get_default_evaluation(self) -> Dict:
        """Return default evaluation structure on error"""
        return {
            "total_score": 0,
            "breakdown": {
                "frontend": 0,
                "backend": 0,
                "code_quality": 0,
                "git_practices": 0,
                "individual_contributions": 0
            },
            "individual_scores": {},
            "strengths": ["Unable to evaluate"],
            "weaknesses": ["Evaluation failed - check logs"],
            "recommendations": ["Please review the repository manually"],
            "detailed_feedback": "Automated evaluation encountered an error. Manual review recommended."
        }
    
    def cleanup_clone(self, local_path: str):
        """Remove cloned repository to free space"""
        try:
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
                logger.info(f"Cleaned up {local_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {local_path}: {e}")
