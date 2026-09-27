from pydantic import BaseModel


class UserRegistration(BaseModel):
    name:str
    email:str
    phone:str
    password:str