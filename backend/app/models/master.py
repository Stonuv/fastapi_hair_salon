import uuid
from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Master(Base):
    __tablename__ = "masters"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True),
                            ForeignKey("users.id", ondelete="CASCADE"),
                            nullable=False, unique=True)
    specialization = Column(String(200))
    photo_url      = Column(String(500))
    # Финальная цена = services.price * coefficient
    # (если не задан price_override в master_services)
    coefficient    = Column(Numeric(4, 2), nullable=False, default=1.00)
    is_active      = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("coefficient > 0", name="ck_masters_coefficient_positive"),
    )

    # Связи
    user         = relationship("User",        back_populates="master_profile")
    services     = relationship("MasterService", back_populates="master",
                                cascade="all, delete-orphan")
    schedules    = relationship("Schedule",    back_populates="master",
                                cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="master",
                                foreign_keys="Appointment.master_id")

    def __repr__(self):
        return f"<Master(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class MasterService(Base):
    """Связь N:M — какой мастер оказывает какую услугу."""
    __tablename__ = "master_services"

    master_id      = Column(UUID(as_uuid=True),
                            ForeignKey("masters.id",  ondelete="CASCADE"),
                            primary_key=True)
    service_id     = Column(UUID(as_uuid=True),
                            ForeignKey("services.id", ondelete="CASCADE"),
                            primary_key=True)
    # NULL → итоговая цена = services.price * masters.coefficient
    price_override = Column(Numeric(10, 2))

    __table_args__ = (
        CheckConstraint("price_override >= 0", name="ck_master_services_price_override_non_negative"),
    )

    # Связи
    master  = relationship("Master",  back_populates="services")
    service = relationship("Service", back_populates="masters")

    def __repr__(self):
        return (f"<MasterService(master_id={self.master_id}, "
                f"service_id={self.service_id}, override={self.price_override})>")
