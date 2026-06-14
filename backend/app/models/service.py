import uuid
from sqlalchemy import Column, String, Text, Boolean, Numeric, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Service(Base):
    __tablename__ = "services"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(200), nullable=False)
    description  = Column(Text)
    price        = Column(Numeric(10, 2), nullable=False)
    duration_min = Column(Integer, nullable=False)
    is_active    = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("price >= 0",        name="ck_services_price_non_negative"),
        CheckConstraint("duration_min > 0",  name="ck_services_duration_positive"),
    )

    # Связи
    masters      = relationship("MasterService", back_populates="service",
                                cascade="all, delete-orphan")
    appointments = relationship("Appointment",   back_populates="service")

    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.name}', price={self.price})>"
