from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..repositories.service_repository import ServiceRepository
from ..schemas.pagination import PageResponse
from ..schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate


class ServiceService:
    def __init__(self, db: Session):
        self.service_repo = ServiceRepository(db)

    def list_paginated(
        self, *, page: int, page_size: int,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        is_active: bool | None = None,
        sort_by: Literal["name", "price", "duration_min"] = "name",
        sort_order: Literal["asc", "desc"] = "asc",
    ) -> PageResponse[ServiceResponse]:
        services, total = self.service_repo.list_paginated(
            page=page, page_size=page_size, search=search,
            min_price=min_price, max_price=max_price, is_active=is_active,
            sort_by=sort_by, sort_order=sort_order,
        )
        return PageResponse[ServiceResponse](
            items=[ServiceResponse.model_validate(s) for s in services],
            total=total, page=page, page_size=page_size,
        )

    def get_by_id(self, service_id: UUID) -> ServiceResponse:
        service = self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Услуга {service_id} не найдена",
            )
        return ServiceResponse.model_validate(service)

    def create(self, data: ServiceCreate) -> ServiceResponse:
        service = self.service_repo.create(data)
        return ServiceResponse.model_validate(service)

    def update(self, service_id: UUID, data: ServiceUpdate) -> ServiceResponse:
        service = self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Услуга {service_id} не найдена",
            )
        service = self.service_repo.update(service, data)
        return ServiceResponse.model_validate(service)
