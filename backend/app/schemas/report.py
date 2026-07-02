from datetime import date as date_

from pydantic import BaseModel, ConfigDict

from .fields import MoneyOut


class DailyRevenue(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date_
    revenue: MoneyOut


class ServiceReportRow(BaseModel):
    service_name: str
    appointments: int


class MasterReportRow(BaseModel):
    master_name: str
    appointments: int
    revenue: MoneyOut
    avg_check: MoneyOut
    avg_rating: float | None


class ReportResponse(BaseModel):
    date_from: date_
    date_to: date_
    total_revenue: MoneyOut
    total_appointments: int
    avg_check: MoneyOut
    repeat_clients_pct: float
    revenue_by_day: list[DailyRevenue]
    appointments_by_service: list[ServiceReportRow]
    masters_breakdown: list[MasterReportRow]
