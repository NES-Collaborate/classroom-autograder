"""Module for grading submissions."""

from pathlib import Path
from typing import Any

import pandas as pd

from core import logger
from core.classroom import grade_submission, return_submission
from core.email import EmailSender
from core.stringfy import AttachmentParser
from core.users import get_user_profile
from models import (
    Attachment,
    Course,
    CourseWork,
    FeedbackResult,
    Submission,
    UserProfile,
)

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
        send_email_copy: bool = False,
        return_grades: bool = False,
    ):
        """Inicializa o avaliador de submissões."""
        self.classroom_service = classroom_service
        self.drive_service = drive_service
        self.course = course
        self.coursework = coursework
        self.criteria_path = criteria_path
        self.output_dir = output_dir
        self.return_grades = return_grades
        self.email_sender = (
            EmailSender.get_instance(send_email_copy) if send_email else None
        )

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
    ) -> FeedbackResult | None:
        """Processa uma submissão individual."""

        if not attachments:
            self._log_error(
                student.full_name,
                "Nenhum arquivo encontrado",
            )
            return None

        student_submitted_context = self._get_submitted_context(attachments)
        result = create_feedback(student, student_submitted_context, self.criteria_path)

        if isinstance(result, str):
            self._log_error(student.full_name, result)
            return None

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
            elif self.return_grades:
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
        if self.email_sender:
            self.email_sender.send(
                student.email,
                result,
                course=self.course,
                coursework=self.coursework,
            )

        return result

    def _process_submissions_batch(self, submissions: list[Submission]) -> dict:
        """Processa um lote de submissões."""
        stats = {
            "total": len(submissions),
            "processados": 0,
            "erros": 0,
            "notas": [],
            "alunos": [],
        }

        total = len(submissions)
        for idx, submission in enumerate(submissions, 1):
            print()
            logger.info(f"[bold]Processando submissão {idx}/{total}[/bold]")
            student_id = submission.userId
            student = get_user_profile(self.classroom_service, student_id)
            if student is None:
                self._log_error(student_id, "Usuário não encontrado")
                continue

            logger.info(
                f"[bold cyan]➤ {student.full_name}[/bold cyan] ({student.email})"
            )

            try:
                if (
                    not submission.assignmentSubmission
                    or not submission.assignmentSubmission.attachments
                ):
                    self._log_error(student_id, "Nenhum arquivo encontrado")
                    stats["erros"] += 1
                    continue

                result = self._process_submission(
                    submission, student, submission.assignmentSubmission.attachments
                )

                if result and result.grade is not None:
                    stats["notas"].append(result.grade)
                    stats["alunos"].append(
                        {
                            "Nome": student.full_name,
                            "Email": student.email,
                            "Nota": result.grade,
                            "Status": submission.state.value,
                            "Data de Submissão": submission.updateTime.split("T")[0],
                            "Atraso": "Sim" if submission.late else "Não",
                        }
                    )
                    stats["processados"] += 1

            except Exception as e:
                self._log_error(student.full_name, f"Erro: {str(e)}")
                stats["erros"] += 1

        return stats

    def grade(self) -> None:
        """Processa e avalia as submissões de uma atividade."""
        try:
            submissions = self._get_submissions()
            if not submissions:
                logger.warning("Nenhuma submissão encontrada")
                return

            stats = self._process_submissions_batch(submissions)

            # Gera relatório Excel
            if stats["alunos"]:
                # Ordena por nome e formata o DataFrame
                df = pd.DataFrame(stats["alunos"])
                df = df.sort_values("Nome")

                excel_path = self.output_dir / "relatorio_notas.xlsx"
                with pd.ExcelWriter(excel_path, engine="openpyxl", mode="w") as writer:
                    df.to_excel(writer, index=False, sheet_name="Notas")

                    # Obtém a planilha para formatação
                    ws = writer.sheets["Notas"]

                    # Ajusta largura das colunas
                    for column in ws.columns:
                        max_length = 0
                        column_name = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except Exception:
                                pass
                        adjusted_width = max_length + 2
                        ws.column_dimensions[column_name].width = adjusted_width

                    # Formata cabeçalho
                    for cell in ws[1]:
                        cell.font = cell.font.copy(bold=True)
                        cell.fill = cell.fill.copy(
                            patternType="solid", fgColor="E2E2E2"
                        )

                logger.info(f"[green]📊 Relatório salvo em {excel_path}[/green]")

            # Exibe estatísticas
            logger.info("\n[bold]📊 Estatísticas da Avaliação:[/bold]")
            logger.info(f"Total de submissões: {stats['total']}")
            logger.info(f"Submissões processadas: {stats['processados']}")

            if stats["notas"]:
                notas = stats["notas"]
                media = sum(notas) / len(notas)
                maior_nota = max(notas)
                menor_nota = min(notas)

                # Distribuição das notas
                ranges = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10)]
                logger.info("\n[bold cyan]Distribuição das notas:[/bold cyan]")
                logger.info(f"Média: {media:.1f}")
                logger.info(f"Maior nota: {maior_nota:.1f}")
                logger.info(f"Menor nota: {menor_nota:.1f}")

                for inicio, fim in ranges:
                    count = sum(1 for nota in notas if inicio <= nota < fim)
                    perc = count / len(notas) * 100
                    logger.info(f"Entre {inicio} e {fim}: {count} alunos ({perc:.1f}%)")

            logger.info(f"\nTaxa de erros: {(stats['erros'] / stats['total']):.1%}")

            logger.success("✨ Concluído!")

        except Exception as e:
            logger.error(f"Erro ao processar submissões: {str(e)}")
            raise
