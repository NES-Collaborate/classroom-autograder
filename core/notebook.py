"""Module for processing Jupyter notebooks."""

from typing import Any

import nbformat
from rich.console import Console

console = Console()


def extract_cells(notebook: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrai células de código e markdown do notebook."""
    cells = []
    for cell in notebook.get("cells", []):
        if cell["cell_type"] in ["code", "markdown"]:
            cells.append(
                {
                    "type": cell["cell_type"],
                    "source": cell["source"],
                    "outputs": cell.get("outputs", [])
                    if cell["cell_type"] == "code"
                    else [],
                }
            )
    return cells


def process_notebook(notebook_stream: bytes) -> list[dict[str, Any]] | None:
    """Processa um notebook Jupyter e retorna suas células."""
    try:
        notebook = nbformat.reads(notebook_stream.decode("utf-8"), as_version=4)
    except Exception as e:
        console.print(f"[red]Erro ao ler notebook: {str(e)}[/red]")
        return None

    return extract_cells(notebook)
