# Quick Setup Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables
```bash
cp .env.example .env
```

Then edit `.env` and fill in:
- `GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- `SPREADSHEET_ID` - From your Google Sheet URL
- `GITHUB_TOKEN` (optional) - From https://github.com/settings/tokens

### Step 3: Set Up Google Service Account

1. Go to https://console.cloud.google.com/
2. Enable Google Sheets API and Google Drive API
3. Create Service Account → Download JSON
4. Save as `credentials/service_account.json`
5. Share your Google Sheet with the service account email

### Step 4: Prepare Your Google Sheet

| Column A | Column B | Column C | Column D | Column E |
|----------|----------|----------|----------|----------|
| Repo URL | Team Name | Score | Feedback | Contributors |
| https://github.com/user/repo1 | Team 1 | | | |
| https://github.com/user/repo2 | Team 2 | | | |

### Step 5: Run Evaluation
```bash
python scripts/evaluate_github_repos.py
```

## 📊 What Gets Evaluated?

✅ Frontend code (React, Vue, HTML/CSS)  
✅ Backend code (Node.js, Python, Java)  
✅ Database design  
✅ API structure  
✅ Code quality & documentation  
✅ Git commit history  
✅ Individual contributions  

## 🎯 Output

- **Column C**: Overall score (0-100)
- **Column D**: Detailed feedback with breakdown
- **Column E**: Individual contributor statistics

## ⚡ Pro Tips

1. **Add GitHub Token**: Get 5,000 API requests/hour instead of 60
2. **Public Repos Only**: Private repos need token with access
3. **Check Logs**: View `logs/github_evaluation.log` for details
4. **Disk Space**: Repos are auto-deleted after evaluation

## 🔧 Troubleshooting

**Error: GEMINI_API_KEY not set**
→ Add your Gemini API key to `.env`

**Error: Service account file not found**
→ Download from Google Cloud Console and save as `credentials/service_account.json`

**Error: Permission denied on Google Sheets**
→ Share your sheet with the service account email (found in JSON file)

**Error: GitHub rate limit**
→ Add `GITHUB_TOKEN` to `.env`

## 📝 Customization

Want to change evaluation criteria? Edit:
```
src/github_evaluator.py → evaluate_project() method
```

Need different column layout? Edit:
```
.env → REPO_LINK_COLUMN, SCORE_COLUMN, etc.
```

---

**Need Help?** Check the full README.md for detailed documentation.
