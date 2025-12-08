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
        logger.info("Google API handler ready")
    
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
        """Read rows from Google Sheet with retry logic"""
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=Config.SPREADSHEET_ID,
                range=range_name
            ).execute()
            rows = result.get("values", [])
            logger.info(f"Read {len(rows)} rows from sheet")
            return rows
        except Exception as e:
            logger.error(f"Error reading sheet: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def extract_doc_text(self, doc_id: str) -> str:
        """Extract full text from Google Doc"""
        try:
            doc = self.docs_service.documents().get(documentId=doc_id).execute()
            text_parts = []
            
            for element in doc.get("body", {}).get("content", []):
                if "paragraph" in element:
                    for text_run in element["paragraph"].get("elements", []):
                        content = text_run.get("textRun", {}).get("content", "")
                        if content.strip():
                            text_parts.append(content)
                
                elif "table" in element:
                    for row in element["table"].get("tableRows", []):
                        for cell in row.get("tableCells", []):
                            for cell_content in cell.get("content", []):
                                if "paragraph" in cell_content:
                                    for text_run in cell_content["paragraph"].get("elements", []):
                                        content = text_run.get("textRun", {}).get("content", "")
                                        if content.strip():
                                            text_parts.append(content)
            
            full_text = "".join(text_parts).strip()
            logger.info(f"Extracted {len(full_text)} characters from doc {doc_id}")
            return full_text
        
        except Exception as e:
            logger.error(f"Error extracting text from doc {doc_id}: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def write_to_sheet(self, row_number: int, score: str, feedback: str):
        """Write evaluation results back to sheet"""
        try:
            range_name = f"{Config.SCORE_COLUMN}{row_number}:{Config.FEEDBACK_COLUMN}{row_number}"
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=Config.SPREADSHEET_ID,
                range=range_name,
                valueInputOption="RAW",
                body={"values": [[score, feedback]]}
            ).execute()
            logger.info(f"Updated row {row_number} with results")
        except Exception as e:
            logger.error(f"Error writing to sheet row {row_number}: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def write_to_cell(self, cell_notation: str, value: str):
        """Write a single value to a specific cell (e.g., 'C2', 'D5')"""
        try:
            range_name = f"{Config.SHEET_NAME}!{cell_notation}"
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=Config.SPREADSHEET_ID,
                range=range_name,
                valueInputOption="RAW",
                body={"values": [[value]]}
            ).execute()
            logger.info(f"Updated cell {cell_notation}")
        except Exception as e:
            logger.error(f"Error writing to cell {cell_notation}: {e}")
            raise
    
    def get_doc_metadata(self, doc_id: str) -> Dict:
        """Get document metadata including title and last modified"""
        try:
            file = self.drive_service.files().get(
                fileId=doc_id,
                fields="name,modifiedTime,createdTime,owners"
            ).execute()
            return file
        except Exception as e:
            logger.warning(f"Could not fetch metadata for doc {doc_id}: {e}")
            return {}
