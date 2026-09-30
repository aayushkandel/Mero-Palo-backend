from fastapi import APIRouter,Depends,status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.dtos import UpdateUserProfile,UserRegistration,UserRegisterResponse,UserLogin,UpdateUserProfileResponse,ChangePassword
from src.utils.db import get_db
from src.users import controller
from src.utils import is_auth
from src.users.models import User
from src.utils.is_auth import is_user_authenticated

user_routes= APIRouter(prefix="/users")

@user_routes.post("/register", status_code=status.HTTP_201_CREATED,response_model=UserRegisterResponse)
async def register(body:UserRegistration,db:AsyncSession=Depends(get_db)):
    return await controller.register(body,db)

@user_routes.post("/login",status_code=status.HTTP_200_OK)
async def login(body:UserLogin,db:AsyncSession=Depends(get_db)):
    return await controller.login_user(body,db)

@user_routes.get("/is_auth",status_code=status.HTTP_200_OK)
async def user_authenticate(request:Request, db:AsyncSession = Depends(get_db)):
    return await  is_auth.is_user_authenticated(request,db)



# get user profile
@user_routes.get("/profile",status_code=status.HTTP_200_OK)
async def get_user_profile(user:User=Depends(is_user_authenticated)):
    return  controller.get_user_profile(user)

# update user profile

@user_routes.put("/update",response_model=UpdateUserProfileResponse,status_code=status.HTTP_200_OK)
async def update_user_profile(body:UpdateUserProfile,db:AsyncSession=Depends(get_db),user:User=Depends(is_user_authenticated)):
    return await controller.update_profile(body,db,user)

#delete user
@user_routes.delete("/delete",status_code=status.HTTP_200_OK)
async def delete_user(db:AsyncSession=Depends(get_db),user:User=Depends(is_user_authenticated)):
    return await controller.delete_user(db, user)

# change password

@user_routes.put("/change_password",status_code=status.HTTP_200_OK)
async def password_change(body:ChangePassword,db:AsyncSession=Depends(get_db),user:User=Depends(is_user_authenticated)):
    return await controller.change_password(body,db,user)