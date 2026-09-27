from fastapi import APIRouter,Depends,status,Request
from sqlalchemy.orm import Session
from src.users.dtos import UpdateUserProfile,UserRegistration,UserRegisterResponse,UserLogin,UpdateUserProfileResponse,ChangePassword
from src.utils.db import get_db
from src.users import controller
from src.utils import is_auth
from src.users.models import User
from src.utils.is_auth import is_user_authenticated,is_admin_authenticated

user_routes= APIRouter(prefix="/users")

@user_routes.post("/register", status_code=status.HTTP_201_CREATED,response_model=UserRegisterResponse)
def register(body:UserRegistration,db:Session=Depends(get_db)):
    return controller.register(body,db)

@user_routes.post("/login",status_code=status.HTTP_200_OK)
def login(body:UserLogin,db:Session=Depends(get_db)):
    return controller.login_user(body,db)

@user_routes.get("/is_auth",status_code=status.HTTP_200_OK)
def user_authenticate(request:Request, db:Session = Depends(get_db)):
    return is_auth.is_user_authenticated(request,db)

@user_routes.get("/is_admin_auth",status_code=status.HTTP_200_OK)
def admin_authenticate(request:Request, db:Session = Depends(get_db)):
    return is_auth.is_admin_authenticated(request,db)

# get user profile
@user_routes.get("/profile",status_code=status.HTTP_200_OK)
def get_user_profile(user:User=Depends(is_user_authenticated)):
    return controller.get_user_profile(user)

# update user profile

@user_routes.put("/update",response_model=UpdateUserProfileResponse,status_code=status.HTTP_200_OK)
def update_user_profile(body:UpdateUserProfile,db:Session=Depends(get_db),user:User=Depends(is_user_authenticated)):
    return controller.update_profile(body,db,user)

#delete user
@user_routes.delete("/delete",status_code=status.HTTP_200_OK)
def delete_user(db:Session=Depends(get_db),user:User=Depends(is_user_authenticated)):
    return controller.delete_user(db, user)

# change password

@user_routes.put("/change_password",status_code=status.HTTP_200_OK)
def password_change(body:ChangePassword,db:Session=Depends(get_db),user:User=Depends(is_user_authenticated)):
    return controller.change_password(body,db,user)