"""Google Drive integration module."""

import io
from typing import Optional

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from rich.console import Console

console = Console()


def download_file(
    file_id: str, drive_service: ..., silent: bool = False
) -> Optional[bytes]:
    """
    Download arquivo do Google Drive com progresso.

    Args:
        file_id: ID do arquivo no Drive
        drive_service: Serviço autenticado do Google Drive
        silent: Se True, não exibe progresso do download

    Returns:
        Bytes do arquivo ou None se houver erro
    """
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            if not silent:
                console.print(
                    f"Download: [blue]{int(status.progress() * 100)}%[/blue]",
                    end="\r",
                )

        if not silent:
            console.print()

        return file.getvalue()

    except HttpError as error:
        console.print(f"[red]Erro ao baixar arquivo: {str(error)}[/red]")
        return None

    except Exception as e:
        console.print(f"[red]Erro inesperado: {str(e)}[/red]")
        return None
