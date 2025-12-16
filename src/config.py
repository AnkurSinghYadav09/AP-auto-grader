import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

def get_config_value(key: str, default: str = None) -> str:
    if HAS_STREAMLIT:
        try:
            return st.secrets.get(key, os.getenv(key, default))
        except (AttributeError, FileNotFoundError):
            return os.getenv(key, default)
    return os.getenv(key, default)

class Config:
    BASE_DIR = Path(__file__).parent.parent
    CREDENTIALS_DIR = BASE_DIR / "credentials"
    LOGS_DIR = BASE_DIR / "logs"
    RUBRICS_DIR = BASE_DIR / "rubrics"

    try:
        LOGS_DIR.mkdir(exist_ok=True)
        CREDENTIALS_DIR.mkdir(exist_ok=True)
        RUBRICS_DIR.mkdir(exist_ok=True)
    except (OSError, PermissionError):
        pass

    AI_PROVIDER = get_config_value("AI_PROVIDER", "gemini").lower()
    OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
    OPENAI_MODEL = get_config_value("OPENAI_MODEL", "gpt-4-turbo-preview")
    GEMINI_API_KEY = get_config_value("GEMINI_API_KEY")
    GEMINI_MODEL = get_config_value("GEMINI_MODEL", "gemini-1.5-flash")
    GITHUB_TOKEN = get_config_value("GITHUB_TOKEN")
    CLONE_DIR = get_config_value("CLONE_DIR", "cloned_repos")
    SPREADSHEET_ID = get_config_value("SPREADSHEET_ID")
    SHEET_NAME = get_config_value("SHEET_NAME", "Sheet1")
    SERVICE_ACCOUNT_FILE = get_config_value("SERVICE_ACCOUNT_FILE", "credentials/service_account.json")
    DOC_LINK_COLUMN = get_config_value("DOC_LINK_COLUMN", "A")
    STUDENT_NAME_COLUMN = get_config_value("STUDENT_NAME_COLUMN", "B")
    SCORE_COLUMN = get_config_value("SCORE_COLUMN", "C")
    FEEDBACK_COLUMN = get_config_value("FEEDBACK_COLUMN", "D")
    REPO_LINK_COLUMN = get_config_value("REPO_LINK_COLUMN", "A")
    TEAM_NAME_COLUMN = get_config_value("TEAM_NAME_COLUMN", "B")
    CONTRIBUTORS_COLUMN = get_config_value("CONTRIBUTORS_COLUMN", "E")
    MAX_WORKERS = int(get_config_value("MAX_WORKERS", "5"))
    RETRY_ATTEMPTS = int(get_config_value("RETRY_ATTEMPTS", "3"))
    BATCH_SIZE = int(get_config_value("BATCH_SIZE", "10"))
    INCLUDE_PLAGIARISM_CHECK = get_config_value("INCLUDE_PLAGIARISM_CHECK", "True").lower() == "true"
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/documents.readonly"
    ]

    @classmethod
    def validate(cls):
        errors = []
        if cls.AI_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY not set (AI_PROVIDER is 'gemini')")
        elif cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY not set (AI_PROVIDER is 'openai')")
        elif cls.AI_PROVIDER == "deepseek" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY not set (AI_PROVIDER is 'deepseek')")
        if not cls.SPREADSHEET_ID:
            errors.append("SPREADSHEET_ID not set")
        if HAS_STREAMLIT:
            try:
                has_secrets = "gcp_service_account" in st.secrets
                has_file = Path(cls.SERVICE_ACCOUNT_FILE).exists()
                if not has_secrets and not has_file:
                    errors.append(f"Service account not found: credentials/service_account.json")
            except (AttributeError, FileNotFoundError):
                if not Path(cls.SERVICE_ACCOUNT_FILE).exists():
                    errors.append(f"Service account file not found: {cls.SERVICE_ACCOUNT_FILE}")
        else:
            if not Path(cls.SERVICE_ACCOUNT_FILE).exists():
                errors.append(f"Service account file not found: {cls.SERVICE_ACCOUNT_FILE}")
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
        return True
