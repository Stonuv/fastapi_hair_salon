from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID

from ..repositories.service_repository import ServiceRepository
from ..schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse, ServiceListResponse


class ServiceService:
    def __init__(self, db: Session):
        self.service_repo = ServiceRepository(db)

    def get_all(self) -> ServiceListResponse:
        services = self.service_repo.get_all_active()
        return ServiceListResponse(
            services=[ServiceResponse.model_validate(s) for s in services],
            total=len(services),
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
