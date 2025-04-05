"""Module for grading submissions."""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from .notebook import process_notebook

console = Console()


def download_file(drive_service: Any, file_id: str) -> Optional[str]:
    """Download arquivo do Google Drive."""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = drive_service.http.MediaIoBaseDownload(file, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return file.getvalue().decode("utf-8")
    except Exception as e:
        console.print(f"[red]Erro ao baixar arquivo {file_id}: {str(e)}[/red]")
        return None


def get_submissions(
    classroom_service: Any, course_id: str, assignment_id: str
) -> List[Dict[str, Any]]:
    """Busca submissões de uma atividade."""
    try:
        results = (
            classroom_service.courses()
            .courseWork()
            .studentSubmissions()
            .list(courseId=course_id, courseWorkId=assignment_id)
            .execute()
        )
        return results.get("studentSubmissions", [])
    except Exception as e:
        console.print(f"[red]Erro ao buscar submissões: {str(e)}[/red]")
        return []


def save_feedback(output_dir: Path, student_id: str, feedback: str) -> None:
    """Salva feedback em arquivo markdown."""
    try:
        student_file = output_dir / f"{student_id}_feedback.md"
        student_file.write_text(feedback, encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Erro ao salvar feedback: {str(e)}[/red]")


def log_error(output_dir: Path, student_id: str, error: str) -> None:
    """Registra erro no arquivo de erros."""
    try:
        error_file = output_dir / "errors.md"
        error_content = f"\n## Aluno: {student_id}\n{error}\n"

        if error_file.exists():
            current_content = error_file.read_text(encoding="utf-8")
            error_file.write_text(current_content + error_content, encoding="utf-8")
        else:
            error_file.write_text(
                f"# Log de Erros\n\n{error_content}", encoding="utf-8"
            )
    except Exception as e:
        console.print(f"[red]Erro ao registrar erro: {str(e)}[/red]")


def grade_submissions(
    classroom_service: Any,
    drive_service: Any,
    course_id: str,
    assignment_id: str,
) -> None:
    """Processa e avalia as submissões de uma atividade."""
    try:
        # 1. Criar diretório de saída
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # 2. Buscar submissões
        submissions = get_submissions(classroom_service, course_id, assignment_id)
        if not submissions:
            console.print("[yellow]Nenhuma submissão encontrada.[/yellow]")
            return

        # 3. Processar cada submissão
        # TODO: refatorar dividindo em funções menores
        for submission in submissions:
            student_id = submission.get("userId")
            if not student_id:
                continue

            try:
                # Recupera arquivo anexado
                attachments = submission.get("assignmentSubmission", {}).get(
                    "attachments", []
                )
                if not attachments:
                    log_error(
                        output_dir,
                        student_id,
                        "### Erro: Submissão sem anexos\n- Nenhum arquivo encontrado",
                    )
                    continue

                # Processa primeiro anexo (assume um único notebook)
                print(submission)
                exit()
                drive_file = attachments[0].get("driveFile", {})
                file_id = drive_file.get("id")
                if not file_id:
                    log_error(
                        output_dir,
                        student_id,
                        "### Erro: Anexo inválido\n- ID do arquivo não encontrado",
                    )
                    continue

                # Download e processamento do notebook
                content = download_file(drive_service, file_id)
                if not content:
                    log_error(
                        output_dir,
                        student_id,
                        "### Erro: Download falhou\n- Não foi possível baixar o arquivo",
                    )
                    continue

                # Salva notebook temporariamente
                temp_file = output_dir / f"{student_id}_temp.ipynb"
                temp_file.write_text(content, encoding="utf-8")

                # Processa células
                cells = process_notebook(temp_file)
                temp_file.unlink()  # Remove arquivo temporário

                if not cells:
                    log_error(
                        output_dir,
                        student_id,
                        "### Erro: Notebook inválido\n- Não foi possível processar o notebook",
                    )
                    continue

                # Avalia com LLM
                from .llm import create_feedback

                # TODO: Implementar leitura do arquivo de critérios
                criteria_file = None
                feedback = create_feedback(student_id, cells, criteria_file)

                save_feedback(output_dir, student_id, feedback)

            except Exception as e:
                log_error(
                    output_dir,
                    student_id,
                    f"### Erro: Exceção não tratada\n- {str(e)}",
                )

        console.print("[green]✨ Processamento concluído![/green]")

    except Exception as e:
        console.print(f"[red]Erro ao processar submissões: {str(e)}[/red]")
        raise
