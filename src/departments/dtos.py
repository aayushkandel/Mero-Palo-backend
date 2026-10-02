from pydantic import BaseModel

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

