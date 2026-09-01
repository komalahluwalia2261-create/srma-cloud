"""
Google Drive implementation of StorageAdapter.

Auth: OAuth 2.0 installed-app flow (per-user consent) via
google-auth-oauthlib. Service-account auth is also supported for shared
review folders — see `from_service_account`.

Scopes requested are read/write on Drive files the user explicitly shares
with the app (`drive.file`), not blanket Drive access. This matters for the
paper's data-governance section: the tool should never request broader
Drive permissions than the review folder it operates on.
"""

from __future__ import annotations

import io
from typing import Iterable, Optional

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .base import FileRef, ScreeningDecision, StorageAdapter

# Narrowest scope that supports listing/reading files the app created or
# was explicitly given access to, plus Sheets for the decision log.
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/x-research-info-systems",  # .ris
}


class GoogleDriveAdapter(StorageAdapter):
    def __init__(self, credentials: Credentials):
        self._drive = build("drive", "v3", credentials=credentials)
        self._sheets = build("sheets", "v4", credentials=credentials)

    # ---- construction helpers -------------------------------------------------

    @classmethod
    def from_oauth_flow(cls, client_secrets_path: str, token_cache_path: Optional[str] = None) -> "GoogleDriveAdapter":
        """Interactive per-user auth. Caches the refresh token if a path is given."""
        creds = None
        if token_cache_path:
            try:
                creds = Credentials.from_authorized_user_file(token_cache_path, SCOPES)
            except FileNotFoundError:
                creds = None
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
            if token_cache_path:
                with open(token_cache_path, "w") as f:
                    f.write(creds.to_json())
        return cls(creds)

    @classmethod
    def from_service_account(cls, key_path: str) -> "GoogleDriveAdapter":
        """Non-interactive auth for a shared review folder (CI, scheduled runs)."""
        creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
        return cls(creds)

    # ---- StorageAdapter interface ----------------------------------------------

    def list_new_files(self, folder_ref: str, since: Optional[str] = None) -> Iterable[FileRef]:
        query = f"'{folder_ref}' in parents and trashed = false"
        if since:
            query += f" and modifiedTime > '{since}'"

        page_token = None
        while True:
            response = (
                self._drive.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                    pageToken=page_token,
                )
                .execute()
            )
            for f in response.get("files", []):
                if f["mimeType"] not in SUPPORTED_MIME_TYPES:
                    continue
                yield FileRef(
                    id=f["id"],
                    name=f["name"],
                    mime_type=f["mimeType"],
                    modified_time=f["modifiedTime"],
                    size_bytes=int(f["size"]) if "size" in f else None,
                )
            page_token = response.get("nextPageToken")
            if not page_token:
                break

    def fetch_file(self, file_ref: FileRef) -> bytes:
        request = self._drive.files().get_media(fileId=file_ref.id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()

    def write_decision(self, decision: ScreeningDecision, destination_ref: str) -> None:
        """Appends a row to a tracking Google Sheet.

        `destination_ref` is the spreadsheetId of a sheet with a header row:
        file_id | file_name | stage | decision | rationale | model | modified_time
        """
        row = [
            decision.file_ref.id,
            decision.file_ref.name,
            decision.stage,
            decision.decision,
            decision.rationale,
            decision.model_name,
            decision.file_ref.modified_time,
        ]
        self._sheets.spreadsheets().values().append(
            spreadsheetId=destination_ref,
            range="A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
