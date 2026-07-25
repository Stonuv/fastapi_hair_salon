from uuid import UUID

from fastapi import HTTPException, status

from ..models.enums import UserRole
from ..models.user import User


def resolve_salon_scope(current_user: User, salon_id_param: UUID | None) -> UUID | None:
    """None = вся сеть (доступно только owner). Для admin — всегда его
    salon_id; чужой salon_id в параметре — явный 403, а не тихая подмена.

    Вызывать только за уже-admin-или-owner-гейтом (get_current_admin) — для
    client/master/анонимного вызывающего salon_id_param остаётся обычным
    публичным фильтром без ownership-проверки (см. GET /api/masters)."""
    if current_user.role == UserRole.owner:
        return salon_id_param
    if salon_id_param is not None and salon_id_param != current_user.salon_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Доступен только собственный салон")
    return current_user.salon_id
