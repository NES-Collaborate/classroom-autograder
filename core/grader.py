"""Module for grading submissions."""

from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn

from classroom.drive import download_file
from classroom.users import get_user_profile

from .notebook import process_notebook

console = Console()


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
    output_dir: Path,
    student_id: str,
    attachments: List[Dict[str, Any]],
) -> None:
    """Processa uma submissão individual."""
    # Obtém perfil do usuário
    profile = get_user_profile(classroom_service, student_id)
    student_name = profile["full_name"] if profile else student_id

    if not attachments:
        log_error(
            output_dir,
            student_name,
            "### Erro: Submissão sem anexos\n- Nenhum arquivo encontrado",
        )
        return

    # Processa primeiro anexo (assume um único notebook)
    drive_file = attachments[0].get("driveFile", {})
    file_id = drive_file.get("id")
    if not file_id:
        log_error(
            output_dir,
            student_name,
            "### Erro: Anexo inválido\n- ID do arquivo não encontrado",
        )
        return

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

    # TODO: Implementar leitura do arquivo de critérios
    criteria_file = None
    feedback = create_feedback(student_id, cells, criteria_file)

    save_feedback(output_dir, student_id, student_name, feedback)


def prepare_output_dir() -> Path:
    """Prepara diretório de saída."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def process_submissions_batch(
    classroom_service: Any,
    drive_service: Any,
    output_dir: Path,
    submissions: List[Dict[str, Any]],
    progress: Progress,
) -> None:
    """Processa um lote de submissões com barra de progresso."""
    task = progress.add_task("Processando submissões...", total=len(submissions))

    for submission in submissions:
        student_id = submission.get("userId")
        if not student_id:
            progress.advance(task)
            continue

        try:
            attachments = submission.get("assignmentSubmission", {}).get(
                "attachments", []
            )
            process_submission(
                classroom_service, drive_service, output_dir, student_id, attachments
            )

        except Exception as e:
            # Obtém nome do aluno para o erro
            profile = get_user_profile(classroom_service, student_id)
            student_name = profile["full_name"] if profile else student_id
            log_error(
                output_dir,
                student_name,
                f"### Erro: Exceção não tratada\n- {str(e)}",
            )

        progress.advance(task)


def grade_submissions(
    classroom_service: Any,
    drive_service: Any,
    course_id: str,
    assignment_id: str,
) -> None:
    """Processa e avalia as submissões de uma atividade."""
    try:
        # 1. Preparar ambiente
        output_dir = prepare_output_dir()

        # 2. Buscar submissões
        submissions = get_submissions(classroom_service, course_id, assignment_id)
        if not submissions:
            console.print("[yellow]Nenhuma submissão encontrada.[/yellow]")
            return

        # 3. Processar submissões
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            console=console,
        ) as progress:
            process_submissions_batch(
                classroom_service, drive_service, output_dir, submissions, progress
            )

        console.print("[green]✨ Processamento concluído![/green]")

    except Exception as e:
        console.print(f"[red]Erro ao processar submissões: {str(e)}[/red]")
        raise
