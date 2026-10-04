from pydantic import BaseModel
from datetime import date

class CreateToken(BaseModel):
    dates:date
    patient_name:str
    patient_address:str
    patient_age:int
    patient_phone:str

class GetByDate(BaseModel):
    dates:date