"""Google Drive integration module."""

import io
from typing import Optional

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from core import logger


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
        if not silent:
            logger.info(f"Iniciando download do arquivo {file_id}...")

        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            if not silent:
                logger.info(
                    f"Download em progresso: {int(status.progress() * 100)}%",
                )

        if not silent:
            logger.success("Download concluído com sucesso")
        return file.getvalue()

    except HttpError as error:
        logger.error(f"Erro ao baixar arquivo: {str(error)}")
        return None

    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return None
