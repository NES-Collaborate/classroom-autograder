from pathlib import Path

from core import logger
from core.llm import generate_criteria
from core.stringfy import AttachmentParser
from models import CourseWork


class CriteriaGenerator:
    def __init__(
        self,
        course_work: CourseWork,
        drive_service: ...,
        output_dir: Path,
    ) -> None:
        """Inicializa o gerador de critérios."""
        self.course_work = course_work
        self.drive_service = drive_service
        self.output_dir = output_dir

    def generate(self) -> Path:
        criteria_path = self.output_dir / "criteria.md"
        if criteria_path.exists():
            logger.warning(
                f"O arquivo [bold]{criteria_path}[/bold] já existe. Será utilizado o arquivo existente."
            )
            return criteria_path

        attachments = self.course_work.materials or []
        context = f"# Contexto da Atividade\nTítulo: {self.course_work.title}\nDescrição: {self.course_work.description}\nNota Máxima: {self.course_work.maxPoints}\n\n"

        if attachments:
            context += "# Materiais\n"
            for attachment in attachments:
                attachment_parser = AttachmentParser(
                    attachment, self.drive_service, self.output_dir
                )
                context += attachment_parser.stringfy() + "\n\n"

        # TODO: tornar processo interativo perguntando ao usuário se deseja modificar de alguma forma o que foi gerado.
        with logger.status("Gerando critérios de avaliação..."):
            generated_criteria = generate_criteria(context)

        criteria_path.write_text(generated_criteria)

        logger.preview(
            generated_criteria, title="[bold blue]📋 Critérios Gerados[/bold blue]"
        )

        return criteria_path
