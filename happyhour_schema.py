from pydantic import BaseModel, Field
from typing import List, Literal
from enum import Enum

class WeekDay(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

class Schedule(BaseModel):
    days: List[WeekDay] = Field(
        description="Days of the week when this happy hour session is available."
    )
    times: str = Field(
        description="Time range during which this happy hour session occurs."
    )
    
    class Config:
        extra = "forbid"  # This corresponds to additionalProperties: false

class Deal(BaseModel):
    item: str = Field(
        description="Name of the food or drink item."
    )
    description: str = Field(
        description="Any further details about the food or drink item."
    )
    deal: str = Field(
        description="Details of the deal for the item."
    )
    
    class Config:
        extra = "forbid"

class HappyHourSession(BaseModel):
    name: str = Field(
        description="The name of the happy hour session."
    )
    schedule: Schedule
    deals: List[Deal] = Field(
        description="List of deals available during this happy hour session. Intelligently identify different schedules if there are more than one kind of happy hours with different times and/or weekday ranges"
    )
    
    class Config:
        extra = "forbid"

class HappyHour(BaseModel):
    happy_hours: List[HappyHourSession] = Field(
        description="List of happy hour sessions with individual schedules and deals. Identify the schedule and look for different schedules and days of happy hours that might have different times or deals."
    )
    
    class Config:
        extra = "forbid"
