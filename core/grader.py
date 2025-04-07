"""Module for grading submissions."""

from pathlib import Path
from typing import Any

from core import logger
from core.classroom import grade_submission, return_submission
from core.email import EmailSender
from core.stringfy import AttachmentParser
from core.users import get_user_profile
from models import Attachment, Course, CourseWork, Submission, UserProfile

from .llm import create_feedback


class SubmissionsGrader:
    """Classe responsável por gerenciar a avaliação de submissões."""

    def __init__(
        self,
        classroom_service: Any,
        drive_service: Any,
        course: Course,
        coursework: CourseWork,
        criteria_path: Path,
        output_dir: Path,
        send_email: bool = False,
        return_grades: bool = False,
    ):
        """Inicializa o avaliador de submissões."""
        self.classroom_service = classroom_service
        self.drive_service = drive_service
        self.course = course
        self.coursework = coursework
        self.criteria_path = criteria_path
        self.output_dir = output_dir
        self.send_email = send_email
        self.return_grades = return_grades

    def _get_submissions(self) -> list[Submission]:
        """Busca submissões de uma atividade."""
        try:
            results = (
                self.classroom_service.courses()
                .courseWork()
                .studentSubmissions()
                .list(courseId=self.course.id, courseWorkId=self.coursework.id)
                .execute()
            )
            return [
                Submission.model_validate(submission)
                for submission in results.get("studentSubmissions", [])
            ]
        except Exception as e:
            logger.error(f"Erro ao buscar submissões: {str(e)}")
            return []

    def _save_feedback(self, student: UserProfile, feedback: str) -> None:
        """Salva feedback em arquivo markdown."""
        try:
            student_file = (
                self.output_dir / f"{student.id}_{student.full_name}_feedback.md"
            )
            student_file.write_text(feedback, encoding="utf-8")
        except Exception as e:
            logger.error(f"Erro ao salvar feedback: {str(e)}")

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
            logger.error(f"Erro ao registrar erro: {str(e)}")

    def _get_submitted_context(self, attachments: list[Attachment]) -> str:
        """Retorna em formato de string o contexto de tudo que foi submetido."""
        return "\n\n".join(
            AttachmentParser(attachment, self.drive_service, self.output_dir).stringfy()
            for attachment in attachments
        )

    def _process_submission(
        self,
        submission: Submission,
        student: UserProfile,
        attachments: list[Attachment],
    ) -> None:
        """Processa uma submissão individual."""

        if not attachments:
            self._log_error(
                student.full_name,
                "Nenhum arquivo encontrado",
            )
            return

        student_submitted_context = self._get_submitted_context(attachments)

        # TODO: adicionar informações adicionais sobre o enunciado da atividade, pontuação, etc.
        result = create_feedback(student, student_submitted_context, self.criteria_path)

        if isinstance(result, str):
            self._log_error(student.full_name, result)
            return

        # Salva o feedback
        self._save_feedback(student, result.feedback)

        # Processa notas
        if submission.associatedWithDeveloper:
            logger.info(f"[bold green]Nota {result.grade}[/bold green]")
            success = grade_submission(
                self.classroom_service,
                self.course.id,
                self.coursework.id,
                submission.id,
                result.grade,
                result.grade if self.return_grades else None,
            )
            if not success:
                logger.error("❌ Falha ao atribuir nota")

            if self.return_grades and success:
                return_submission(
                    self.classroom_service,
                    self.course.id,
                    self.coursework.id,
                    submission.id,
                )
        else:
            logger.warning(
                "[yellow]Nota não definida (atividade de outra conta)[/yellow]"
            )

        # Send email if requested
        if self.send_email:
            email_sender = EmailSender.get_instance()

            email_sender.send(
                student.email,
                result,
                course=self.course,
                coursework=self.coursework,
            )

    def _process_submissions_batch(self, submissions: list[Submission]) -> None:
        """Processa um lote de submissões."""
        for submission in submissions:
            student_id = submission.userId
            student = get_user_profile(self.classroom_service, student_id)
            if student is None:
                self._log_error(student_id, "Usuário não encontrado")
                continue

            # Nome do aluno em destaque
            print()
            logger.info(
                f"[bold cyan]➤ {student.full_name}[/bold cyan] ({student.email})"
            )

            try:
                if (
                    not submission.assignmentSubmission
                    or not submission.assignmentSubmission.attachments
                ):
                    self._log_error(student.full_name, "Nenhum arquivo encontrado")
                    continue

                self._process_submission(
                    submission, student, submission.assignmentSubmission.attachments
                )

            except Exception as e:
                self._log_error(student.full_name, f"Erro: {str(e)}")

    def grade(self) -> None:
        """Processa e avalia as submissões de uma atividade."""
        try:
            submissions = self._get_submissions()
            if not submissions:
                logger.warning("Nenhuma submissão encontrada")
                return

            self._process_submissions_batch(submissions)
            logger.success("✨ Concluído!")

        except Exception as e:
            logger.error(f"Erro ao processar submissões: {str(e)}")
            raise


def grade_submissions(
    classroom_service: Any,
    drive_service: Any,
    course: Course,
    coursework: CourseWork,
    criteria_path: Path,
    output_dir: Path,
    send_email: bool = False,
    return_grades: bool = False,
) -> None:
    """Função de conveniência para processar e avaliar submissões."""
    grader = SubmissionsGrader(
        classroom_service,
        drive_service,
        course,
        coursework,
        criteria_path,
        output_dir,
        send_email,
        return_grades,
    )
    grader.grade()
