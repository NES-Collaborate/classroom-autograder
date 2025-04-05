"""Google Classroom users module."""

from typing import Any, Dict, Optional

from rich.console import Console

console = Console()


def get_user_profile(classroom_service: Any, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtém o perfil do usuário do Google Classroom.

    Args:
        classroom_service: Serviço autenticado do Google Classroom
        user_id: ID do usuário

    Returns:
        Dict com informações do usuário ou None se houver erro
    """
    try:
        profile = classroom_service.userProfiles().get(userId=user_id).execute()
        return {
            "id": profile["id"],
            "full_name": profile["name"]["fullName"],
            "email": profile.get("emailAddress", ""),
        }
    except Exception as e:
        console.print(
            f"[yellow]Aviso: Não foi possível carregar perfil do usuário {user_id}: {str(e)}[/yellow]"
        )
        return None
