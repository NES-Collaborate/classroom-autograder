"""Core module initialization."""

from rich.console import Console
from rich.markdown import Markdown
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)


class ConsoleLogger:
    """Centralized logging utility for consistent console output."""

    def __init__(self):
        self.console = Console()

    def info(self, message: str):
        """Display an information message."""
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def success(self, message: str):
        """Display a success message."""
        self.console.print(f"[green]✓[/green] {message}")

    def warning(self, message: str):
        """Display a warning message."""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def error(self, message: str):
        """Display an error message."""
        self.console.print(f"[red]✕[/red] {message}")

    def progress(self, description: str) -> Progress:
        """Create a progress bar with standard styling."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        )

    def status(self, message: str):
        """Display a status message with spinner."""
        return self.console.status(f"[cyan]⋯[/cyan] {message}")

    def preview(self, content: str, title: str | None = None):
        """Display a preview of markdown content."""
        if title:
            self.console.print(f"\n[bold blue]{title}:[/bold blue]")
        md = Markdown(content[:500] + "..." if len(content) > 500 else content)
        self.console.print(md)


logger = ConsoleLogger()
