"""Google Classroom users module."""

from typing import Any, Optional

from core import logger
from models import UserProfile


def get_user_profile(classroom_service: Any, user_id: str) -> Optional[UserProfile]:
    """
    Obtém o perfil do usuário do Google Classroom.

    Args:
        classroom_service: Serviço autenticado do Google Classroom
        user_id: ID do usuário

    Returns:
        UserProfile com informações do usuário ou None se houver erro
    """
    try:
        profile = classroom_service.userProfiles().get(userId=user_id).execute()
        return UserProfile(
            id=profile["id"],
            full_name=profile["name"]["fullName"],
            email=profile.get("emailAddress", ""),
        )
    except Exception as e:
        logger.warning(
            f"Não foi possível carregar perfil do usuário {user_id}: {str(e)}"
        )
        return None
