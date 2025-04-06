from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from core.classroom import get_course_work
from core.llm import generate_criteria
from core.stringfy import AttachmentParser


class CriteriaGenerator:
    def __init__(
        self,
        course_id: str,
        assignment_id: str,
        classroom_service: ...,
        drive_service: ...,
        output_dir: Path,
    ) -> None:
        self.console = Console()

        with self.console.status("[bold green]Buscando informações da atividade..."):
            course_work = get_course_work(classroom_service, course_id, assignment_id)

        if course_work is None:
            self.console.print(
                Panel("[bold red]Erro ao buscar o contexto da atividade.", title="Erro")
            )
            raise ValueError("Erro ao buscar o contexto da atividade.")

        self.console.print(
            Panel(
                f"[bold green]Atividade encontrada: [/bold green][white]{course_work.title}",
                title="Sucesso",
            )
        )

        self.course_work = course_work
        self.drive_service = drive_service
        self.output_dir = output_dir

    def generate(self) -> Path:
        attachments = self.course_work.materials or []

        self.console.print("\n[bold blue]Preparando contexto da atividade[/bold blue]")

        context = f"# Contexto da Atividade\nTítulo: {self.course_work.title}\nDescrição: {self.course_work.description}\nNota Máxima: {self.course_work.maxPoints}\n\n"
        if attachments:
            context += "# Materiais\n"
            self.console.print(
                f"[yellow]Processando {len(attachments)} materiais anexados[/yellow]"
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
            ) as progress:
                task = progress.add_task(
                    "[cyan]Processando anexos...", total=len(attachments)
                )

                for attachment in attachments:
                    progress.update(
                        task,
                        advance=1,
                        description=f"Processando {getattr(attachment, 'title', 'anexo')}",
                    )
                    attachment_parser = AttachmentParser(
                        attachment, self.drive_service, self.output_dir
                    )
                    context += attachment_parser.stringfy() + "\n\n"
        else:
            self.console.print("[yellow]Nenhum material anexado encontrado[/yellow]")

        self.console.print(
            "\n[bold green]Gerando critérios de avaliação...[/bold green]"
        )

        with self.console.status(
            "[bold cyan]Aguardando resposta do modelo de linguagem..."
        ):
            # TODO: tornar processo interativo perguntando ao usuário se deseja modificar de alguma forma o que foi gerado.
            generated_criteria = generate_criteria(context)

        criteria_path = self.output_dir / "criteria.md"
        criteria_path.write_text(generated_criteria)

        self.console.print(
            f"\n[bold green]Critérios de avaliação gerados e salvos em:[/bold green] {criteria_path}"
        )

        self.console.print("\n[bold blue]Preview dos critérios gerados:[/bold blue]")
        self.console.print(
            Panel(
                Markdown(
                    generated_criteria[:500] + "..."
                    if len(generated_criteria) > 500
                    else generated_criteria
                )
            )
        )

        return criteria_path
