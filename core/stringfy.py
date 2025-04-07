from pathlib import Path
from typing import Callable, Optional

from core import logger
from core.drive import download_file
from models import Attachment, DriveFile, Form, Link, SharedDriveFile, YouTubeVideo
from utils import sanitize_string

from .notebook import process_notebook


class AttachmentParser:
    """
    Parser para anexos que converte vários tipos de anexos em formato de string.
    Trata diferentes tipos de arquivos (arquivos do drive, vídeos do YouTube, links, formulários) e os processa
    adequadamente, incluindo o download e análise de formatos específicos de arquivos como notebooks.
    """

    def __init__(self, attachment: Attachment, drive_service: ..., output_dir: Path):
        self.attachment = attachment
        self.drive_service = drive_service
        self.output_dir = output_dir / "downloads"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def __download_drive_file(
        self, drive_file: DriveFile, filename: str
    ) -> Optional[bytes]:
        file_path = self.output_dir / filename
        if file_path.exists():
            with file_path.open("rb") as f:
                return f.read()

        file_bytes = download_file(drive_file.id, self.drive_service, silent=True)
        if file_bytes is None:
            return

        file_path.write_bytes(file_bytes)
        return file_bytes

    def __parse_bare_text(self, bytes: bytes) -> str:
        try:
            return bytes.decode("utf-8")
        except UnicodeDecodeError:
            return bytes.decode("latin-1")
        except Exception as e:
            raise ValueError(f"Erro ao decodificar bytes: {str(e)}")

    def __stringfy_drive_file(self, drive_file: DriveFile | SharedDriveFile) -> str:
        if isinstance(drive_file, SharedDriveFile):
            drive_file = drive_file.driveFile

        logger.info(f"[dim]📄 {drive_file.title}[/dim]")
        filename = f"{drive_file.id}_{sanitize_string(drive_file.title)}"
        file_bytes = self.__download_drive_file(drive_file, filename)
        if file_bytes is None:
            return f"[Erro ao processar arquivo: {drive_file.title}]"

        file_extension = Path(filename).suffix.lstrip(".")
        file_parsers = {
            "ipynb": process_notebook,
        }

        parsed_file = file_parsers.get(file_extension, self.__parse_bare_text)(
            file_bytes
        )
        return f"{drive_file.title}\n{parsed_file}"

    # TODO: implementar demais parsers
    def __stringfy_youtube_video(self, youtube_video: YouTubeVideo) -> str: ...

    def __stringfy_link(self, link: Link) -> str: ...

    def __stringfy_form(self, form: Form) -> str: ...

    def stringfy(self) -> str:
        attachment_stringfiers: dict[str, Callable] = {
            "driveFile": self.__stringfy_drive_file,
            "youTubeVideo": self.__stringfy_youtube_video,
            "link": self.__stringfy_link,
            "form": self.__stringfy_form,
        }

        for attachment_type, stringfier in attachment_stringfiers.items():
            if (value := getattr(self.attachment, attachment_type)) is not None:
                return stringfier(value)

        return ""
