"""Module for processing Jupyter notebooks."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import nbformat
from rich.console import Console

console = Console()


def read_notebook(file_path: Path) -> Optional[Dict[str, Any]]:
    """Lê e retorna o conteúdo de um notebook Jupyter."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        return notebook
    except Exception as e:
        console.print(f"[red]Erro ao ler notebook {file_path}: {str(e)}[/red]")
        return None


def extract_cells(notebook: Dict[str, Any]) -> List[Dict[str, Any]]:
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


def process_notebook(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Processa um notebook Jupyter e retorna suas células."""
    notebook = read_notebook(file_path)
    if notebook:
        return extract_cells(notebook)
    return None
