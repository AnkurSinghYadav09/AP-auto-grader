import logging
from typing import Optional, Dict, List
from googleapiclient.discovery import build
from google.oauth2 import service_account
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import Config

logger = logging.getLogger(__name__)

class GoogleAPIHandler:
    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_file(
            Config.SERVICE_ACCOUNT_FILE,
            scopes=Config.SCOPES
        )
        
        self._sheets_service = None
        self._docs_service = None
        self._drive_service = None

    @property
    def sheets_service(self):
        if self._sheets_service is None:
            self._sheets_service = build("sheets", "v4", credentials=self.creds, cache_discovery=False)
        return self._sheets_service

    @property
    def docs_service(self):
        if self._docs_service is None:
            self._docs_service = build("docs", "v1", credentials=self.creds, cache_discovery=False)
        return self._docs_service

    @property
    def drive_service(self):
        if self._drive_service is None:
            self._drive_service = build("drive", "v3", credentials=self.creds, cache_discovery=False)
        return self._drive_service

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def read_sheet_rows(self, range_name: str) -> List[List[str]]:
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=Config.SPREADSHEET_ID,
            range=range_name
        ).execute()
        rows = result.get("values", [])
        return rows

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def write_to_sheet(self, row_number: int, score: str, feedback: str):
        range_name = f"{Config.SCORE_COLUMN}{row_number}:{Config.FEEDBACK_COLUMN}{row_number}"
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=Config.SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body={"values": [[score, feedback]]}
        ).execute()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def write_to_cell(self, cell_notation: str, value: str):
        range_name = f"{Config.SHEET_NAME}!{cell_notation}"
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=Config.SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body={"values": [[value]]}
        ).execute()

    def get_doc_metadata(self, doc_id: str) -> Dict:
        file = self.drive_service.files().get(
            fileId=doc_id,
            fields="name,modifiedTime,createdTime,owners"
        ).execute()
        return file
