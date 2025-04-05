"""Module for grading submissions."""

from pathlib import Path
from typing import Any, List

from rich.console import Console

from classroom.drive import download_file
from classroom.users import get_user_profile
from models import Attachment, Submission, UserProfile

from .llm import create_feedback
from .notebook import process_notebook

console = Console()


class SubmissionsGrader:
    """Classe responsável por gerenciar a avaliação de submissões."""

    def __init__(
        self,
        classroom_service: Any,
        drive_service: Any,
        course_id: str,
        assignment_id: str,
        criteria_path: Path,
    ):
        """Inicializa o avaliador de submissões."""
        self.classroom_service = classroom_service
        self.drive_service = drive_service
        self.course_id = course_id
        self.assignment_id = assignment_id
        self.criteria_path = criteria_path
        self.output_dir = self._prepare_output_dir()

    def _prepare_output_dir(self) -> Path:
        """Prepara diretório de saída."""
        output_dir = Path("output") / self.course_id / self.assignment_id
        output_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Feedbacks serão salvos em: {output_dir}[/green]")
        return output_dir

    def _get_submissions(self) -> List[Submission]:
        """Busca submissões de uma atividade."""
        try:
            results = (
                self.classroom_service.courses()
                .courseWork()
                .studentSubmissions()
                .list(courseId=self.course_id, courseWorkId=self.assignment_id)
                .execute()
            )
            return [
                Submission.model_validate(submission)
                for submission in results.get("studentSubmissions", [])
            ]
        except Exception as e:
            console.print(f"[red]Erro ao buscar submissões: {str(e)}[/red]")
            return []

    def _save_feedback(self, student_id: str, student_name: str, feedback: str) -> None:
        """Salva feedback em arquivo markdown."""
        try:
            student_file = self.output_dir / f"{student_id}_{student_name}_feedback.md"
            student_file.write_text(feedback, encoding="utf-8")
        except Exception as e:
            console.print(f"[red]Erro ao salvar feedback: {str(e)}[/red]")

    def _log_error(self, student_name: str, error: str) -> None:
        """Registra erro no arquivo de erros."""
        try:
            error_file = self.output_dir / "errors.md"
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

    def _process_submission(
        self,
        student: UserProfile,
        attachments: List[Attachment],
    ) -> None:
        """Processa uma submissão individual."""

        if not attachments:
            self._log_error(
                student.full_name,
                "### Erro: Submissão sem anexos\n- Nenhum arquivo encontrado",
            )
            return

        # TODO: processar todas as submissões de todos os tipos (drivefile, form, link, youtubevideo)
        # Processa primeiro anexo (assume um único notebook)
        drive_file = attachments[0].driveFile
        if drive_file is None:
            self._log_error(
                student.full_name,
                "### Erro: Anexo inválido\n- Arquivo não encontrado",
            )
            return

        file_id = drive_file.id

        # TODO: tornar esta função mais geral, não necessáriamente teremos somente um jupyternotebook.
        # Download e processamento do notebook
        content = download_file(self.drive_service, file_id, silent=True)
        if not content:
            self._log_error(
                student.full_name,
                "### Erro: Download falhou\n- Não foi possível baixar o arquivo",
            )
            return

        # Salva notebook temporariamente
        temp_file = self.output_dir / f"{student.id}_{student.full_name}_temp.ipynb"
        temp_file.write_bytes(content)

        # Processa células
        cells = process_notebook(temp_file)
        temp_file.unlink()  # Remove arquivo temporário

        if not cells:
            self._log_error(
                student.full_name,
                "### Erro: Notebook inválido\n- Não foi possível processar o notebook",
            )
            return

        # TODO: reescrever esse "create_feedback" para receber como arugmento um "contexto" geral, de todas as subumissões, não só "cells".
        feedback = create_feedback(student.id, cells, self.criteria_path)
        self._save_feedback(student.id, student.full_name, feedback)

    def _process_submissions_batch(self, submissions: List[Submission]) -> None:
        """Processa um lote de submissões."""
        # TODO: ThreadPoolExecutor para processar submissões em paralelo.
        for submission in submissions:
            student_id = submission.userId
            student = get_user_profile(self.classroom_service, student_id)
            if student is None:
                # TODO: mudar isso de erro pra warning e prosseguir com a execução utilizando student placeholder.
                self._log_error(
                    student_id,
                    "### Erro: Usuário inválido\n- Não foi possível encontrar o usuário",
                )
                continue

            try:
                if submission.assignmentSubmission is None:
                    self._log_error(
                        student_id,
                        "### Erro: Submissão inválida\n- Nenhum arquivo encontrado",
                    )
                    continue

                attachments = submission.assignmentSubmission.attachments
                if attachments is None:
                    self._log_error(
                        student_id,
                        "### Erro: Submissão inválida\n- Nenhum arquivo encontrado",
                    )
                    continue

                self._process_submission(student, attachments)

            except Exception as e:
                student_name = student.full_name
                self._log_error(
                    student_name,
                    f"### Erro: Exceção não tratada\n- {str(e)}",
                )

    def grade(self) -> None:
        """Processa e avalia as submissões de uma atividade."""
        try:
            # 1. Buscar submissões
            submissions = self._get_submissions()
            if not submissions:
                console.print("[yellow]Nenhuma submissão encontrada.[/yellow]")
                return

            # 2. Processar submissões
            self._process_submissions_batch(submissions)

            console.print("[green]✨ Processamento concluído![/green]")

        except Exception as e:
            console.print(f"[red]Erro ao processar submissões: {str(e)}[/red]")
            raise


def grade_submissions(
    classroom_service: Any,
    drive_service: Any,
    course_id: str,
    assignment_id: str,
    criteria_path: Path,
) -> None:
    """Função de conveniência para processar e avaliar submissões."""
    grader = SubmissionsGrader(
        classroom_service, drive_service, course_id, assignment_id, criteria_path
    )
    grader.grade()
