# GitHub Project Auto-Grader

An automated system that evaluates fullstack GitHub projects using AI. It clones repositories, analyzes individual contributions, and generates detailed feedback with scores.

## Features

- **Repository Analysis**: Clone and analyze GitHub repositories
- **Contributor Tracking**: Track individual commits, lines added/deleted, and contribution percentages
- **AI Evaluation**: Use Gemini AI to evaluate code quality, frontend, backend, and git practices
- **Google Sheets Integration**: Read repository URLs from sheets and write results back automatically
- **Sequential Processing**: Evaluate projects one at a time with immediate updates

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your credentials:

```env
# Gemini API (Get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=models/gemini-2.5-flash

# GitHub Token (Get from https://github.com/settings/tokens)
GITHUB_TOKEN=your_github_token

# Google Sheet
SPREADSHEET_ID=your_spreadsheet_id
SHEET_NAME=sheet1

# Column Configuration
REPO_LINK_COLUMN=G        # Column with repository URLs
TEAM_NAME_COLUMN=B        # Column with team names
SCORE_COLUMN=J            # Where to write scores
FEEDBACK_COLUMN=K         # Where to write feedback
CONTRIBUTORS_COLUMN=L     # Where to write contributor info
```

### 3. Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create a service account
5. Download credentials JSON
6. Save as `credentials/service_account.json`
7. Share your Google Sheet with the service account email

### 4. Run Evaluation

```bash
# Test with a single repository
python scripts/evaluate_single_repo.py "https://github.com/user/repo" --team "TeamName"

# Evaluate all repositories from Google Sheet
python scripts/evaluate_github_repos.py

# Verify setup
python scripts/verify_setup.py
```

## How It Works

1. **Read**: Gets repository URLs and team names from Google Sheet
2. **Clone**: Clones each repository locally (shallow clone)
3. **Analyze**: Uses GitHub API to analyze contributor statistics
4. **Evaluate**: Sends code to Gemini AI for evaluation
5. **Score**: Generates scores across 5 categories (100 points total)
6. **Write**: Updates Google Sheet with results immediately
7. **Cleanup**: Removes cloned repository

## Evaluation Criteria

- **Frontend** (25 points): UI/UX, components, responsiveness
- **Backend** (25 points): API design, database, security
- **Code Quality** (20 points): Structure, documentation, best practices
- **Git Practices** (15 points): Commits, branching, messages
- **Individual Contributions** (15 points): Workload distribution, participation

## Project Structure

```
ap-auto-grader/
├── src/
│   ├── config.py              # Configuration management
│   ├── github_evaluator.py    # Core evaluation logic
│   └── google_api.py          # Google Sheets integration
├── scripts/
│   ├── evaluate_github_repos.py   # Main batch processor
│   ├── evaluate_single_repo.py    # Single repo tester
│   └── verify_setup.py            # Setup verification
├── credentials/
│   └── service_account.json   # Google service account
├── .env                       # Environment variables
└── requirements.txt           # Python dependencies
```

## Tips

- **Rate Limits**: GitHub API has rate limits. With a token you get 5,000 requests/hour
- **Large Repos**: Very large repositories may take longer to evaluate
- **Gemini API**: Free tier has rate limits. Consider upgrading for large batches
- **Sheet Permissions**: Ensure service account has edit access to your sheet
- **Testing**: Always test with a single repo first before running batch evaluation

## Troubleshooting

**Repository not found**: Check that the URL is correct and the repo is public (or your token has access)

**Sheet write errors**: Verify the sheet name in `.env` matches exactly (case-sensitive)

**GitHub API rate limit**: Wait an hour or use a different GitHub token

**Import errors**: Make sure you activated the virtual environment: `source .venv/bin/activate`

## License

MIT License - feel free to modify and use for your projects.
