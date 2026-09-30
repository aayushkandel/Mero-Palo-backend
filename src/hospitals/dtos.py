from pydantic import BaseModel

class HospitalRegister(BaseModel):
    name:str
    phone:str
    registration_no:str
    password:str
    confirm_password:str

class HospitalLogin(BaseModel):
    phone:str
    password:str

class HospitalProfileUpdate(BaseModel):
    name:str
    email:str
    phone:str
    address:str



class ChangePassword(BaseModel):
    old_password:str
    new_password:str
    confirm_new_password:str