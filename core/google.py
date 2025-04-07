from __future__ import print_function

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from core import logger


def get_service(
    api_name: str,
    api_version: str,
    credentials_path="credentials.json",
    token_dir="tokens",
):
    """Autentica e retorna um serviço da API do Google, com token separado por API."""
    os.makedirs(token_dir, exist_ok=True)
    token_path = os.path.join(token_dir, f"token_{api_name}.json")

    # Escopos por API
    SCOPES_MAP = {
        "classroom": [
            "https://www.googleapis.com/auth/classroom.announcements.readonly",
            "https://www.googleapis.com/auth/classroom.courses.readonly",
            "https://www.googleapis.com/auth/classroom.coursework.me",
            "https://www.googleapis.com/auth/classroom.coursework.students",
            "https://www.googleapis.com/auth/classroom.rosters.readonly",
            "https://www.googleapis.com/auth/classroom.profile.emails",
            "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly",
            "https://www.googleapis.com/auth/classroom.addons.teacher",
        ],
        "drive": [
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    }

    scopes = SCOPES_MAP.get(api_name)
    if not scopes:
        logger.error(f"Escopos não definidos para API: {api_name}")
        raise ValueError(f"Escopos não definidos para API: {api_name}")

    creds = None

    # Apaga o token se escopos mudarem (previne conflitos)
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, scopes)
        except Exception:
            os.remove(token_path)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())
    return build(api_name, api_version, credentials=creds)
