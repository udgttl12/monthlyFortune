from pydantic import BaseModel, Field


class MonthlyHoroscopeResponse(BaseModel):
    career: str = Field(..., description="Career outlook for the month")
    money: str = Field(..., description="Money outlook for the month")
    love: str = Field(..., description="Love outlook for the month")
    risk: str = Field(..., description="Potential risk area for the month")
