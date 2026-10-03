from pydantic import BaseModel
from datetime import date,time
from enum import IntEnum

class DepartmentRegister(BaseModel):
    name:str
    phone:str
    password:str
    department_room_no:str
    confirm_password:str

class DepartmentLogin(BaseModel):
    phone:str
    password:str

class DepartmentUpdate(BaseModel):
    name:str
    phone:str
    department_room_no:str


class OpenStatus(IntEnum):
    Open=0
    Close=1

class ScheduleCreate(BaseModel):
    dates:list[date]
    registration_start: time | None=None
    registration_close: time | None=None
    token_start: time | None=None
    open_status:OpenStatus

class ScheduleDate(BaseModel):
    dates:date