from datetime import date as date_

from pydantic import BaseModel, ConfigDict


class DailyRevenue(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date_
    revenue: float


class ServiceReportRow(BaseModel):
    service_name: str
    appointments: int


class MasterReportRow(BaseModel):
    master_name: str
    appointments: int
    revenue: float
    avg_check: float
    avg_rating: float | None


class ReportResponse(BaseModel):
    date_from: date_
    date_to: date_
    total_revenue: float
    total_appointments: int
    avg_check: float
    repeat_clients_pct: float
    revenue_by_day: list[DailyRevenue]
    appointments_by_service: list[ServiceReportRow]
    masters_breakdown: list[MasterReportRow]
