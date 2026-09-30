from pydantic import BaseModel


class UserRegistration(BaseModel):
    name:str
    phone:str
    password:str
    confirm_password:str

class UserRegisterResponse(BaseModel):
    message:str = "User register successful"
    name:str

class UserLogin(BaseModel):
    phone:str
    password:str

class UpdateUserProfile(BaseModel):
    name:str
    email:str
    address:str
    phone:str


class UpdateUserProfileResponse(BaseModel):
        message:str = "Profile updated successfully"
        name:str
        email:str
        address:str
        phone:str

class ChangePassword(BaseModel):
     old_password:str
     new_password:str
     confirm_new_password:str

