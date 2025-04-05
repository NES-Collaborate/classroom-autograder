"""Module for grading submissions."""

from pathlib import Path
from typing import Any

from rich.console import Console

from classroom.drive import download_file
from classroom.users import get_user_profile
from models.classroom import Attachment, Submission

from .notebook import process_notebook

console = Console()


def get_submissions(
    classroom_service: Any, course_id: str, assignment_id: str
) -> list[Submission]:
    """Busca submissões de uma atividade."""
    try:
        results = (
            classroom_service.courses()
            .courseWork()
            .studentSubmissions()
            .list(courseId=course_id, courseWorkId=assignment_id)
            .execute()
        )
        return [
            Submission.model_validate(submission)
            for submission in results.get("studentSubmissions", [])
        ]
    except Exception as e:
        console.print(f"[red]Erro ao buscar submissões: {str(e)}[/red]")
        return []


def save_feedback(
    output_dir: Path, student_id: str, student_name: str, feedback: str
) -> None:
    """Salva feedback em arquivo markdown."""
    try:
        student_file = output_dir / f"{student_id}_{student_name}_feedback.md"
        student_file.write_text(feedback, encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Erro ao salvar feedback: {str(e)}[/red]")


def log_error(output_dir: Path, student_name: str, error: str) -> None:
    """Registra erro no arquivo de erros."""
    try:
        error_file = output_dir / "errors.md"
        error_content = f"\n## Aluno: {student_name}\n{error}\n"

        if error_file.exists():
            current_content = error_file.read_text(encoding="utf-8")
            error_file.write_text(current_content + error_content, encoding="utf-8")
        else:
            error_file.write_text(
                f"# Log de Erros\n\n{error_content}", encoding="utf-8"
            )
    except Exception as e:
        console.print(f"[red]Erro ao registrar erro: {str(e)}[/red]")


def process_submission(
    classroom_service: Any,
    drive_service: Any,
    student: dict,
    attachments: list[Attachment],
    criteria_path: Path,
    output_dir: Path,
) -> None:
    """Processa uma submissão individual."""
    student_id = student["userId"]
    student_name = student["full_name"]

    if not attachments:
        log_error(
            output_dir,
            student_name,
            "### Erro: Submissão sem anexos\n- Nenhum arquivo encontrado",
        )
        return

    # TODO: processar todas as submissões de todos os tipos (drivefile, form, link, youtubevideo)
    # Processa primeiro anexo (assume um único notebook)
    drive_file = attachments[0].driveFile
    if drive_file is None:
        log_error(
            output_dir,
            student_name,
            "### Erro: Anexo inválido\n- Arquivo não encontrado",
        )
        return

    file_id = drive_file.id

    # TODO: tornar esta função mais geral, não necessáriamente teremos somente um jupyternotebook.
    # Download e processamento do notebook
    content = download_file(drive_service, file_id, silent=True)
    if not content:
        log_error(
            output_dir,
            student_name,
            "### Erro: Download falhou\n- Não foi possível baixar o arquivo",
        )
        return

    # Salva notebook temporariamente
    temp_file = output_dir / f"{student_id}_{student_name}_temp.ipynb"
    temp_file.write_bytes(content)

    # Processa células
    cells = process_notebook(temp_file)
    temp_file.unlink()  # Remove arquivo temporário

    if not cells:
        log_error(
            output_dir,
            student_name,
            "### Erro: Notebook inválido\n- Não foi possível processar o notebook",
        )
        return

    # Avalia com LLM
    from .llm import create_feedback

    # TODO: reescrever esse "create_feedback" para receber como arugmento um "contexto" geral, de todas as subumissões, não só "cells".
    feedback = create_feedback(student_id, cells, criteria_path)

    save_feedback(output_dir, student_id, student_name, feedback)


def prepare_output_dir(course_id: str, assignment_id: str) -> Path:
    """Prepara diretório de saída."""
    output_dir = Path("output") / course_id / assignment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Feedbacks serão salvos em: {output_dir}[/green]")
    return output_dir


def process_submissions_batch(
    classroom_service: Any,
    drive_service: Any,
    criteria_path: Path,
    submissions: list[Submission],
    output_dir: Path,
) -> None:
    """Processa um lote de submissões com barra de progresso."""
    # TODO: ThreadPoolExecutor para processar submissões em paralelo.
    for submission in submissions:
        student_id = submission.userId
        student = get_user_profile(classroom_service, student_id)
        if student is None:
            # TODO: mudar isso de erro pra warning e prosseguir com a execução utilizando student placeholder.
            log_error(
                output_dir,
                student_id,
                "### Erro: Usuário inválido\n- Não foi possível encontrar o usuário",
            )
            continue

        try:
            if submission.assignmentSubmission is None:
                log_error(
                    output_dir,
                    student_id,
                    "### Erro: Submissão inválida\n- Nenhum arquivo encontrado",
                )
                continue

            attachments = submission.assignmentSubmission.attachments
            if attachments is None:
                log_error(
                    output_dir,
                    student_id,
                    "### Erro: Submissão inválida\n- Nenhum arquivo encontrado",
                )
                continue

            process_submission(
                classroom_service,
                drive_service,
                student,
                attachments,
                criteria_path,
                output_dir,
            )

        except Exception as e:
            student_name = student["full_name"] if student else student_id
            log_error(
                output_dir,
                student_name,
                f"### Erro: Exceção não tratada\n- {str(e)}",
            )


def grade_submissions(
    classroom_service: Any,
    drive_service: Any,
    course_id: str,
    assignment_id: str,
    criteria_path: Path,
) -> None:
    """Processa e avalia as submissões de uma atividade."""
    try:
        # 1. Preparar ambiente
        output_dir = prepare_output_dir(course_id, assignment_id)

        # 2. Buscar submissões
        submissions = get_submissions(classroom_service, course_id, assignment_id)
        if not submissions:
            console.print("[yellow]Nenhuma submissão encontrada.[/yellow]")
            return

        # 3. Processar submissões
        process_submissions_batch(
            classroom_service,
            drive_service,
            criteria_path,
            submissions,
            output_dir,
        )

        console.print("[green]✨ Processamento concluído![/green]")

    except Exception as e:
        console.print(f"[red]Erro ao processar submissões: {str(e)}[/red]")
        raise
