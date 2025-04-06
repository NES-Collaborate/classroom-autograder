import re


def sanitize_string(string: str) -> str:
    """
    Sanitiza uma string, removendo caracteres especiais e espaços em branco a fim de utilizar como nome de arquivos.

    Args:
        string (str): String a ser sanitizada.

    Returns:
        str: String sanitizada.
    """
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", string).strip()
