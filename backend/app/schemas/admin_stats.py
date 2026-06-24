from datetime import date as date_

from pydantic import BaseModel, ConfigDict


class DailyCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date:  date_
    count: int


class AdminStatsResponse(BaseModel):
    total_users:                 int
    total_clients:               int
    total_masters:               int
    total_services:              int
    appointments_this_month:     int
    revenue_this_month:          float
    registrations_last_30_days:  list[DailyCount]
